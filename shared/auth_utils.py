# shared/auth_utils.py

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
# New imports for password hashing
from passlib.context import CryptContext

from shared.config import get_config, get_env_vars
from shared.jwt_blacklist import is_token_blacklisted

config = get_config()
env = get_env_vars()

# Ensure JWT_SECRET_KEY is loaded
if not env.jwt_secret_key:
    raise ValueError("JWT_SECRET_KEY environment variable not set.")

# Initialize CryptContext for password hashing
# The schemes define the hashing algorithms to use (bcrypt is highly recommended)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{config.services.auth_service.base_path}/token"
)


# --- Password Hashing/Verification Functions ---
def verify_password(plain_password, hashed_password):
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Hashes a plain password."""
    return pwd_context.hash(password)


# -----------------------------------------------


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Use value from config.yml
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=config.jwt.access_token_expire_minutes
        )

    # Add standard JWT claims to make tokens unique and trackable
    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),  # JWT ID for blacklisting
        }
    )

    # Use value from config.yml
    encoded_jwt = jwt.encode(
        to_encode, env.jwt_secret_key, algorithm=config.jwt.algorithm
    )
    return encoded_jwt


async def verify_token(token: str):
    try:
        # First, decode and validate the token structure
        payload = jwt.decode(
            token, env.jwt_secret_key, algorithms=[config.jwt.algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if token is blacklisted (logged out)
        if await is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    """Dependency to get the current authenticated user's ID."""
    user_id = await verify_token(token)
    return user_id


if __name__ == "__main__":
    # Example usage for testing
    test_user_id = "test_user_123"
    token = create_access_token(data={"sub": test_user_id})
    print(f"Generated Token: {token}")

    try:
        decoded_user_id = verify_token(token)
        print(f"Decoded User ID: {decoded_user_id}")
    except HTTPException as e:
        print(f"Error decoding token: {e.detail}")

    # Test password hashing
    plain_pw = "mysecretpassword"
    hashed_pw = get_password_hash(plain_pw)
    print(f"\nHashed password: {hashed_pw}")
    print(
        f"Verify 'mysecretpassword': {verify_password('mysecretpassword', hashed_pw)}"
    )
    print(f"Verify 'wrongpassword': {verify_password('wrongpassword', hashed_pw)}")
