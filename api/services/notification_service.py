"""Business logic for notification management."""

import logging
from typing import Optional

from ..repositories.user_repo import UserRepository
from ..repositories.fridge_repo import FridgeRepository
from ..schemas.fridge_schema import FridgeItemListResponse
from .fridge_service import FridgeService

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Business logic for notification management.

    Responsibilities:
    - Manage notification settings
    - Calculate expiration notifications
    - Schedule notifications
    """

    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo
        self._fridge_repo = FridgeRepository()
        self._fridge_service = FridgeService(
            fridge_repo=self._fridge_repo,
            product_repo=None,
            user_repo=user_repo
        )

    async def get_settings(self, telegram_id: int) -> dict:
        """
        Get user's notification settings.

        Args:
            telegram_id: User's Telegram ID

        Returns:
            Notification settings
        """
        user = await self._user_repo.get_by_telegram_id(telegram_id)

        if not user:
            # Return default settings for non-existent user
            return {
                "enabled": True,
                "days_before": 3,
                "notify_time": "09:00",
                "timezone": "UTC"
            }

        return {
            "enabled": user.notifications_enabled,
            "days_before": user.notifications_days_before,
            "notify_time": user.notifications_time,
            "timezone": user.timezone or "UTC"
        }

    async def update_settings(
        self,
        telegram_id: int,
        enabled: Optional[bool] = None,
        days_before: Optional[int] = None,
        notify_time: Optional[str] = None
    ) -> dict:
        """
        Update user's notification settings.

        Args:
            telegram_id: User's Telegram ID
            enabled: Enable/disable notifications
            days_before: Days before expiration to notify
            notify_time: Notification time (HH:MM)

        Returns:
            Updated notification settings
        """
        user = await self._user_repo.update_notification_settings(
            telegram_id,
            enabled=enabled,
            days_before=days_before,
            notify_time=notify_time
        )

        if not user:
            logger.warning(f"User {telegram_id} not found for settings update")
            return await self.get_settings(telegram_id)

        logger.info(f"Updated notification settings for user {telegram_id}")

        return {
            "enabled": user.notifications_enabled,
            "days_before": user.notifications_days_before,
            "notify_time": user.notifications_time,
            "timezone": user.timezone or "UTC"
        }

    async def get_expiring_items(self, telegram_id: int) -> FridgeItemListResponse:
        """
        Get items that should trigger notification.

        Args:
            telegram_id: User's Telegram ID

        Returns:
            List of expiring items
        """
        settings = await self.get_settings(telegram_id)

        if not settings["enabled"]:
            return FridgeItemListResponse(items=[], total=0)

        # Get items expiring within threshold
        days = settings["days_before"]

        items = await self._fridge_repo.get_expiring_items(telegram_id, days)

        # Convert to response
        from .fridge_service import FridgeService
        fridge_service = FridgeService(
            fridge_repo=self._fridge_repo,
            product_repo=None,
            user_repo=self._user_repo
        )

        response_items = [
            fridge_service._item_to_response(item) for item in items
        ]

        return FridgeItemListResponse(
            items=response_items,
            total=len(response_items)
        )
