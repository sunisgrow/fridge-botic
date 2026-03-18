"""API router for user operations."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas.user_schema import UserCreate, UserResponse
from ..repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def get_user_repo() -> UserRepository:
    """Dependency injection for UserRepository."""
    return UserRepository()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(
    data: UserCreate,
    repo: UserRepository = Depends(get_user_repo)
) -> UserResponse:
    """
    Register new user or get existing one.
    
    Creates default fridge for new users.
    
    Request body:
    - telegram_id: User's Telegram ID (required)
    - username: Telegram username (optional)
    - first_name: User's first name (optional)
    
    Returns user information.
    """
    logger.info(f"Registering user {data.telegram_id}")
    
    try:
        user = await repo.get_or_create(
            telegram_id=data.telegram_id,
            username=data.username,
            first_name=data.first_name
        )
        
        return UserResponse(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            created_at=user.created_at.isoformat() if user.created_at else None,
            timezone=user.timezone,
            language_code=user.language_code
        )
        
    except Exception as e:
        logger.error(f"Failed to register user: {e}")
        raise HTTPException(status_code=500, detail="Failed to register user")


@router.get("/{telegram_id}", response_model=UserResponse)
async def get_user(
    telegram_id: int,
    repo: UserRepository = Depends(get_user_repo)
) -> UserResponse:
    """
    Get user information by Telegram ID.
    
    Path params:
    - telegram_id: User's Telegram ID
    
    Returns user information or 404 if not found.
    """
    logger.info(f"Getting user {telegram_id}")
    
    user = await repo.get_by_telegram_id(telegram_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        created_at=user.created_at.isoformat() if user.created_at else None,
        timezone=user.timezone,
        language_code=user.language_code
    )
