# auth_service/main.py

from datetime import \
    timedelta  # ADD THIS LINE! Or add it to an existing datetime import

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from shared.auth_utils import (create_access_token, get_current_user_id,
                               get_password_hash, verify_password)
from shared.config import get_config
from shared.jwt_blacklist import (blacklist_token, close_jwt_blacklist_redis,
                                  init_jwt_blacklist_redis)
from user_auth.models import SessionLocal, User, create_db_tables
from user_auth.schemas import (PasswordChangeRequest, UserCreate, UserOut,
                               UserProfileResponse, UserProfileUpdate)

# Initialize FastAPI app
app = FastAPI(
    title="Auth Service",
    description="Authentication and User Management Microservice",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Load configuration
config_data = get_config()
auth_service_config = config_data.services.auth_service


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create database tables and initialize JWT blacklist on startup
@app.on_event("startup")
async def startup_event():
    create_db_tables()
    print("MySQL 'users' table created successfully or already exists.")
    await init_jwt_blacklist_redis()
    print("JWT blacklist Redis initialized.")


@app.on_event("shutdown")
async def shutdown_event():
    await close_jwt_blacklist_redis()
    print("JWT blacklist Redis connection closed.")


# Health check endpoint
@app.get(auth_service_config.base_path + "/health", tags=["Health"])
async def health_check():
    return {"status": "Auth Service is healthy!"}


# User registration endpoint
@app.post(
    auth_service_config.base_path + "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists (if provided)
    if user.email:
        db_email = db.query(User).filter(User.email == user.email).first()
        if db_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username, email=user.email, hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- NEW: Login Endpoint to Get JWT Token ---
@app.post(auth_service_config.base_path + "/token", tags=["Auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Authenticate a user and return an access token.
    Expects 'username' and 'password' as form data.
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # You can get expiry minutes from config or default
    access_token_expires = timedelta(
        minutes=config_data.jwt.access_token_expire_minutes
    )
    access_token = create_access_token(
        data={"sub": str(user.id)},  # Use user.id as the subject
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}


# --- Logout Endpoint ---
@app.post(auth_service_config.base_path + "/logout", tags=["Auth"])
async def logout_user(authorization: str = Header(...)):
    """
    Logout user by invalidating their JWT token.
    The token will be added to a blacklist and cannot be used again.
    This logs the user out from all devices/browsers.
    """
    # Extract token from Authorization header
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]

    # Add token to blacklist
    success = await blacklist_token(token)

    if success:
        return {
            "message": "Successfully logged out",
            "detail": "Token has been invalidated and you have been logged out from all devices",
        }
    else:
        # Even if blacklisting fails, we should still return success to the user
        # but log the failure for monitoring
        print("Warning: Token blacklisting failed, but user logout request completed")
        return {
            "message": "Logged out",
            "detail": "Logout completed (blacklist service unavailable)",
        }


# --- Get Current Authenticated User Profile ---
@app.get(
    auth_service_config.base_path + "/users/me",
    response_model=UserProfileResponse,
    tags=["Users"],
)
async def read_users_me(
    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """
    Retrieve the current authenticated user's detailed profile information.
    Requires a valid JWT in the Authorization header.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_updated=user.last_updated.isoformat() if user.last_updated else None,
    )


# --- Update User Profile ---
@app.put(
    auth_service_config.base_path + "/users/me",
    response_model=UserProfileResponse,
    tags=["Users"],
)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Update the current user's profile information (username and/or email).
    Validates uniqueness of username and email.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Validate and update username if provided
    if profile_update.username is not None:
        # Check if username is already taken by another user
        existing_user = (
            db.query(User)
            .filter(User.username == profile_update.username, User.id != user_id)
            .first()
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken",
            )
        user.username = profile_update.username

    # Validate and update email if provided
    if profile_update.email is not None:
        # Check if email is already taken by another user
        existing_email = (
            db.query(User)
            .filter(User.email == profile_update.email, User.id != user_id)
            .first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered",
            )
        user.email = profile_update.email

    # Commit changes
    db.commit()
    db.refresh(user)

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_updated=user.last_updated.isoformat() if user.last_updated else None,
    )


# --- Change User Password ---
@app.post(auth_service_config.base_path + "/users/me/change-password", tags=["Users"])
async def change_password(
    password_change: PasswordChangeRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Change the current user's password.
    Requires the current password for verification.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify current password
    if not verify_password(password_change.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Hash and update new password
    user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


# --- Delete User Account ---
@app.delete(auth_service_config.base_path + "/users/me", tags=["Users"])
async def delete_user_account(
    user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """
    Delete the current user's account (soft delete by setting is_active to False).
    This preserves data integrity while disabling the account.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Soft delete - set is_active to False
    user.is_active = False
    db.commit()

    return {"message": "Account deactivated successfully"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "user_auth.main:app",
        host=auth_service_config.host,  # Use config for host
        port=auth_service_config.port,  # Use config for port
        reload=True,
    )
