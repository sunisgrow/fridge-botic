"""Pydantic schemas for user operations."""

from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base schema for user."""
    telegram_id: int = Field(..., description="User's Telegram ID")
    username: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    created_at: Optional[str] = None
    timezone: str = "UTC"
    language_code: str = "ru"

    class Config:
        from_attributes = True
