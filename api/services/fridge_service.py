"""Business logic for fridge management."""

import logging
from datetime import date
from typing import Optional, List

from ..repositories.fridge_repo import FridgeRepository
from ..repositories.product_repo import ProductRepository
from ..repositories.user_repo import UserRepository
from ..schemas.fridge_schema import (
    FridgeItemCreate,
    FridgeItemUpdate,
    FridgeItemResponse,
    FridgeItemListResponse,
    DeleteReason
)

logger = logging.getLogger(__name__)


class FridgeService:
    """
    Business logic for fridge management.

    Responsibilities:
    - Manage fridge items
    - Calculate expiration warnings
    - Handle product matching
    """

    def __init__(
        self,
        fridge_repo: FridgeRepository,
        product_repo: ProductRepository,
        user_repo: UserRepository
    ):
        self._fridge_repo = fridge_repo
        self._product_repo = product_repo
        self._user_repo = user_repo

    async def get_user_fridge_items(
        self,
        telegram_id: int,
        category_id: Optional[int] = None,
        expiring_days: Optional[int] = None
    ) -> FridgeItemListResponse:
        """
        Get all items in user's fridge with calculated days until expiry.

        Args:
            telegram_id: User's Telegram ID
            category_id: Optional category filter
            expiring_days: Optional filter for expiring items

        Returns:
            List of fridge items with total count
        """
        # Get user's fridge
        fridge = await self._fridge_repo.get_user_fridge(telegram_id)

        if not fridge:
            logger.warning(f"No fridge found for user {telegram_id}")
            return FridgeItemListResponse(items=[], total=0)

        # Get items with filters
        items = await self._fridge_repo.get_fridge_items(
            fridge.id,
            category_id=category_id,
            expiring_days=expiring_days
        )

        # Convert to response
        response_items = [
            self._item_to_response(item) for item in items
        ]

        return FridgeItemListResponse(
            items=response_items,
            total=len(response_items)
        )

    async def add_fridge_item(
        self,
        telegram_id: int,
        data: FridgeItemCreate
    ) -> FridgeItemResponse:
        """
        Add item to user's fridge.

        Args:
            telegram_id: User's Telegram ID
            data: Item creation data

        Returns:
            Created fridge item
        """
        # Get or create user's fridge
        fridge = await self._fridge_repo.get_user_fridge(telegram_id)

        if not fridge:
            # User should exist at this point
            logger.error(f"No fridge found for user {telegram_id}")
            raise ValueError("User fridge not found")

        # Find or create product
        product = await self._product_repo.find_or_create(
            name=data.product_name,
            category_id=data.category_id,
            brand_name=data.brand_name
        )

        # Calculate expiration date if not provided
        expiration_date = data.expiration_date
        if not expiration_date and product.default_shelf_life_days:
            expiration_date = date.today() + date.resolution * product.default_shelf_life_days

        # Add item to fridge
        item = await self._fridge_repo.add_fridge_item(
            fridge_id=fridge.id,
            product_id=product.id,
            quantity=data.quantity,
            expiration_date=expiration_date,
            zone_id=data.zone_id,
            opened=data.opened,
            note=data.note
        )

        logger.info(f"Added {data.product_name} to fridge for user {telegram_id}")

        return self._item_to_response(item)

    async def update_fridge_item(
        self,
        telegram_id: int,
        item_id: int,
        data: FridgeItemUpdate
    ) -> Optional[FridgeItemResponse]:
        """
        Update fridge item.

        Args:
            telegram_id: User's Telegram ID
            item_id: Item ID
            data: Update data

        Returns:
            Updated item or None if not found
        """
        # Verify item belongs to user
        item = await self._fridge_repo.get_fridge_item_by_id(item_id)

        if not item:
            logger.warning(f"Item {item_id} not found")
            return None

        # Get user's fridge to verify ownership
        user_fridge = await self._fridge_repo.get_user_fridge(telegram_id)
        
        if not user_fridge or item.fridge_id != user_fridge.id:
            logger.warning(f"User {telegram_id} cannot access item {item_id}")
            return None

        # Update item
        updated_item = await self._fridge_repo.update_fridge_item(
            item_id=item_id,
            quantity=data.quantity,
            expiration_date=data.expiration_date,
            opened=data.opened,
            note=data.note
        )

        if not updated_item:
            return None

        logger.info(f"Updated item {item_id} for user {telegram_id}")

        return self._item_to_response(updated_item)

    async def delete_fridge_item(
        self,
        telegram_id: int,
        item_id: int,
        reason: Optional[DeleteReason] = None
    ) -> bool:
        """
        Delete fridge item.

        Args:
            telegram_id: User's Telegram ID
            item_id: Item ID
            reason: Deletion reason (for analytics)

        Returns:
            True if deleted, False if not found
        """
        # Verify item belongs to user
        item = await self._fridge_repo.get_fridge_item_by_id(item_id)

        if not item:
            logger.warning(f"Item {item_id} not found")
            return False

        # Get user's fridge to verify ownership
        user_fridge = await self._fridge_repo.get_user_fridge(telegram_id)
        
        if not user_fridge or item.fridge_id != user_fridge.id:
            logger.warning(f"User {telegram_id} cannot access item {item_id}")
            return False

        # TODO: Log deletion reason for analytics

        # Delete item
        deleted = await self._fridge_repo.delete_fridge_item(item_id)

        if deleted:
            logger.info(f"Deleted item {item_id} for user {telegram_id}, reason: {reason}")

        return deleted

    async def get_expiring_items(
        self,
        telegram_id: int,
        days: int = 3
    ) -> FridgeItemListResponse:
        """
        Get items expiring within specified days.

        Args:
            telegram_id: User's Telegram ID
            days: Number of days threshold

        Returns:
            List of expiring items
        """
        items = await self._fridge_repo.get_expiring_items(telegram_id, days)

        response_items = [
            self._item_to_response(item) for item in items
        ]

        return FridgeItemListResponse(
            items=response_items,
            total=len(response_items)
        )

    def _item_to_response(self, item) -> FridgeItemResponse:
        """Convert FridgeItem model to response schema."""
        days_until_expiry = None

        if item.expiration_date:
            delta = item.expiration_date - date.today()
            days_until_expiry = delta.days

        return FridgeItemResponse(
            id=item.id,
            product_name=item.product.name if item.product else "Неизвестный продукт",
            brand=item.product.brand.name if item.product and item.product.brand else None,
            category=item.product.category.name if item.product and item.product.category else None,
            category_icon=item.product.category.icon if item.product and item.product.category else None,
            quantity=item.quantity,
            expiration_date=item.expiration_date,
            days_until_expiry=days_until_expiry,
            added_at=item.added_at.isoformat() if item.added_at else None,
            opened=item.opened,
            note=item.note,
            zone_name=item.zone.name if item.zone else None
        )
