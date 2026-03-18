"""API router for notification operations."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from ..schemas.fridge_schema import FridgeItemListResponse
from ..services.notification_service import NotificationService
from ..repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_notification_service() -> NotificationService:
    """Dependency injection for NotificationService."""
    return NotificationService(user_repo=UserRepository())


@router.get("/settings")
async def get_notification_settings(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    service: NotificationService = Depends(get_notification_service)
) -> dict:
    """
    Get user's notification settings.

    Query params:
    - telegram_id: User's Telegram ID (required)

    Returns notification settings.
    """
    logger.info(f"Getting notification settings for user {telegram_id}")

    settings = await service.get_settings(telegram_id)

    return settings


@router.post("/settings")
async def update_notification_settings(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    enabled: Optional[bool] = Body(None, description="Enable/disable notifications"),
    days_before: Optional[int] = Body(None, description="Days before expiration to notify"),
    notify_time: Optional[str] = Body(None, description="Notification time (HH:MM)"),
    service: NotificationService = Depends(get_notification_service)
) -> dict:
    """
    Update user's notification settings.

    Query params:
    - telegram_id: User's Telegram ID (required)

    Request body:
    - enabled: Enable/disable notifications (optional)
    - days_before: Days before expiration to notify (optional, range: 1-30)
    - notify_time: Notification time in HH:MM format (optional)

    Returns updated settings.
    """
    logger.info(f"Updating notification settings for user {telegram_id}")

    settings = await service.update_settings(
        telegram_id,
        enabled=enabled,
        days_before=days_before,
        notify_time=notify_time
    )

    return settings


@router.get("/expiring", response_model=FridgeItemListResponse)
async def get_expiring_notifications(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    service: NotificationService = Depends(get_notification_service)
) -> FridgeItemListResponse:
    """
    Get items that should trigger notification.

    Query params:
    - telegram_id: User's Telegram ID (required)

    Returns list of items expiring within notification threshold.
    """
    logger.info(f"Getting expiring notifications for user {telegram_id}")

    return await service.get_expiring_items(telegram_id)
