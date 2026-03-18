# -*- coding: utf-8 -*-
"""Repository for user operations."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.session import get_session
from ..models.user import User
from ..models.fridge import Fridge

logger = logging.getLogger(__name__)


class UserRepository:
    """Data access layer for user operations."""

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> User:
        """Create new user with default fridge."""
        async with get_session() as session:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            session.add(user)
            await session.flush()

            # Create default fridge
            fridge = Fridge(
                user_id=user.id,
                name="Main Fridge"
            )
            session.add(fridge)

            await session.commit()
            await session.refresh(user)

            logger.info(f"Created user {telegram_id} with default fridge")

            return user

    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> User:
        """Get existing user or create new one."""
        user = await self.get_by_telegram_id(telegram_id)

        if not user:
            user = await self.create(telegram_id, username, first_name)

        return user

    async def update_notification_settings(
        self,
        telegram_id: int,
        enabled: Optional[bool] = None,
        days_before: Optional[int] = None,
        notify_time: Optional[str] = None
    ) -> Optional[User]:
        """Update user's notification settings."""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {telegram_id} not found")
                return None

            if enabled is not None:
                user.notifications_enabled = enabled
            if days_before is not None:
                user.notifications_days_before = days_before
            if notify_time is not None:
                user.notifications_time = notify_time

            await session.commit()
            await session.refresh(user)

            logger.info(f"Updated notification settings for user {telegram_id}")

            return user
