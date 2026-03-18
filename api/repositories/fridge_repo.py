"""Repository for fridge operations."""

import logging
from datetime import date, timedelta
from typing import Optional, List

from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.session import get_session
from ..models.fridge import Fridge, FridgeItem, FridgeZone
from ..models.product import Product
from ..models.category import Category
from ..models.brand import Brand

logger = logging.getLogger(__name__)


class FridgeRepository:
    """Data access layer for fridge operations."""

    async def get_user_fridge(self, telegram_id: int) -> Optional[Fridge]:
        """Get user's default fridge."""
        async with get_session() as session:
            # Join with users table to find by telegram_id
            from ..models.user import User
            result = await session.execute(
                select(Fridge)
                .join(User, User.id == Fridge.user_id)
                .where(User.telegram_id == telegram_id)
                .options(selectinload(Fridge.items))
            )
            return result.scalar_one_or_none()

    async def get_fridge_items(
        self,
        fridge_id: int,
        category_id: Optional[int] = None,
        expiring_days: Optional[int] = None
    ) -> List[FridgeItem]:
        """
        Get all items in a fridge with optional filters.
        
        Args:
            fridge_id: Fridge ID
            category_id: Filter by category
            expiring_days: Filter items expiring within N days
            
        Returns:
            List of fridge items ordered by expiration date
        """
        async with get_session() as session:
            query = (
                select(FridgeItem)
                .where(FridgeItem.fridge_id == fridge_id)
                .options(
                    selectinload(FridgeItem.product).selectinload(Product.category),
                    selectinload(FridgeItem.product).selectinload(Product.brand),
                    selectinload(FridgeItem.zone)
                )
                .order_by(FridgeItem.expiration_date.asc().nulls_last())
            )

            if category_id:
                query = query.join(Product).where(Product.category_id == category_id)

            if expiring_days is not None:
                target_date = date.today() + timedelta(days=expiring_days)
                # Include both expired (past) and expiring (future within N days)
                query = query.where(
                    and_(
                        FridgeItem.expiration_date.isnot(None),
                        FridgeItem.expiration_date <= target_date
                    )
                )

            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_fridge_item_by_id(self, item_id: int) -> Optional[FridgeItem]:
        """Get fridge item by ID."""
        async with get_session() as session:
            result = await session.execute(
                select(FridgeItem)
                .where(FridgeItem.id == item_id)
                .options(
                    selectinload(FridgeItem.product).selectinload(Product.category),
                    selectinload(FridgeItem.product).selectinload(Product.brand),
                    selectinload(FridgeItem.zone),
                    selectinload(FridgeItem.fridge)
                )
            )
            return result.scalar_one_or_none()

    async def add_fridge_item(
        self,
        fridge_id: int,
        product_id: Optional[int],
        quantity: int = 1,
        expiration_date: Optional[date] = None,
        zone_id: Optional[int] = None,
        opened: bool = False,
        note: Optional[str] = None
    ) -> FridgeItem:
        """
        Add item to fridge.
        
        Args:
            fridge_id: Target fridge ID
            product_id: Product ID (optional for custom products)
            quantity: Item quantity
            expiration_date: Expiration date
            zone_id: Storage zone ID
            opened: Whether item is opened
            note: Custom note
            
        Returns:
            Created fridge item
        """
        async with get_session() as session:
            item = FridgeItem(
                fridge_id=fridge_id,
                product_id=product_id,
                quantity=quantity,
                expiration_date=expiration_date,
                zone_id=zone_id,
                opened=opened,
                note=note
            )
            session.add(item)
            await session.commit()
            await session.refresh(item)
            
            # Reload with relationships
            result = await session.execute(
                select(FridgeItem)
                .where(FridgeItem.id == item.id)
                .options(
                    selectinload(FridgeItem.product).selectinload(Product.category),
                    selectinload(FridgeItem.product).selectinload(Product.brand),
                    selectinload(FridgeItem.zone)
                )
            )
            
            logger.info(f"Added item {item.id} to fridge {fridge_id}")
            return result.scalar_one()

    async def update_fridge_item(
        self,
        item_id: int,
        quantity: Optional[int] = None,
        expiration_date: Optional[date] = None,
        opened: Optional[bool] = None,
        note: Optional[str] = None
    ) -> Optional[FridgeItem]:
        """
        Update fridge item.
        
        Args:
            item_id: Item ID
            quantity: New quantity
            expiration_date: New expiration date
            opened: New opened status
            note: New note
            
        Returns:
            Updated item or None if not found
        """
        async with get_session() as session:
            result = await session.execute(
                select(FridgeItem).where(FridgeItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return None
            
            if quantity is not None:
                item.quantity = quantity
            if expiration_date is not None:
                item.expiration_date = expiration_date
            if opened is not None:
                item.opened = opened
            if note is not None:
                item.note = note
            
            await session.commit()
            await session.refresh(item)
            
            logger.info(f"Updated item {item_id}")
            return item

    async def delete_fridge_item(self, item_id: int) -> bool:
        """
        Delete fridge item.
        
        Args:
            item_id: Item ID
            
        Returns:
            True if deleted, False if not found
        """
        async with get_session() as session:
            result = await session.execute(
                select(FridgeItem).where(FridgeItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            
            if not item:
                return False
            
            await session.delete(item)
            await session.commit()
            
            logger.info(f"Deleted item {item_id}")
            return True

    async def get_expiring_items(
        self,
        telegram_id: int,
        days: int = 3
    ) -> List[FridgeItem]:
        """
        Get items expiring within specified days.
        
        Args:
            telegram_id: User's Telegram ID
            days: Number of days threshold
            
        Returns:
            List of expiring items
        """
        fridge = await self.get_user_fridge(telegram_id)
        
        if not fridge:
            return []
        
        return await self.get_fridge_items(fridge.id, expiring_days=days)

    async def count_fridge_items(self, fridge_id: int) -> int:
        """Count items in fridge."""
        async with get_session() as session:
            result = await session.execute(
                select(func.count(FridgeItem.id))
                .where(FridgeItem.fridge_id == fridge_id)
            )
            return result.scalar() or 0
