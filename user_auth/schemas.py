# auth_service/schemas.py

from typing import Optional

from pydantic import BaseModel, EmailStr, validator


class UserCreate(BaseModel):
    """Schema for user registration input."""

    username: str
    email: str | None = None  # Optional email field
    password: str


class UserOut(BaseModel):
    """Schema for user output, excluding sensitive information like password."""

    id: int
    username: str
    email: str | None = None
    is_active: bool

    class Config:
        # For Pydantic v1: orm_mode = True
        # For Pydantic v2: from_attributes = True
        # Since your venv uses Python 3.11, you're likely on Pydantic v2.
        from_attributes = True  # This tells Pydantic to read ORM models directly


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile information."""

    username: Optional[str] = None
    email: Optional[str] = None

    @validator("username")
    def validate_username(cls, v):
        if v is not None:
            if len(v.strip()) < 3:
                raise ValueError("Username must be at least 3 characters long")
            if len(v.strip()) > 50:
                raise ValueError("Username must be less than 50 characters")
        return v.strip() if v else None

    @validator("email")
    def validate_email(cls, v):
        if v is not None:
            if "@" not in v or "." not in v:
                raise ValueError("Invalid email format")
            if len(v) > 255:
                raise ValueError("Email must be less than 255 characters")
        return v.strip().lower() if v else None


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""

    current_password: str
    new_password: str

    @validator("new_password")
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError("New password must be at least 6 characters long")
        if len(v) > 128:
            raise ValueError("New password must be less than 128 characters")
        return v


class UserProfileResponse(BaseModel):
    """Enhanced schema for user profile response with additional details."""

    id: int
    username: str
    email: str | None = None
    is_active: bool
    created_at: str | None = None  # We'll add this to the model
    last_updated: str | None = None  # We'll add this to the model

    class Config:
        from_attributes = True
