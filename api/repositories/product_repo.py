"""Repository for product operations."""

import logging
from typing import Optional, List

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.session import get_session
from ..models.product import Product
from ..models.category import Category
from ..models.brand import Brand

logger = logging.getLogger(__name__)


class ProductRepository:
    """Data access layer for product operations."""

    async def find_or_create(
        self,
        name: str,
        category_id: Optional[int] = None,
        brand_name: Optional[str] = None
    ) -> Product:
        """
        Find existing product or create new one.

        Args:
            name: Product name
            category_id: Category ID
            brand_name: Brand name

        Returns:
            Product instance
        """
        async with get_session() as session:
            # Try to find existing product
            query = select(Product).where(Product.name.ilike(name))

            if category_id:
                query = query.where(Product.category_id == category_id)

            result = await session.execute(query)
            product = result.scalar_one_or_none()

            if product:
                return product

            # Create new product
            product = Product(
                name=name,
                category_id=category_id
            )

            # Handle brand
            if brand_name:
                brand = await self._get_or_create_brand(session, brand_name)
                product.brand_id = brand.id

            session.add(product)
            await session.commit()
            await session.refresh(product)

            logger.info(f"Created new product: {name}")

            return product

    async def _get_or_create_brand(
        self,
        session: AsyncSession,
        name: str
    ) -> Brand:
        """Get or create brand."""
        result = await session.execute(
            select(Brand).where(Brand.name.ilike(name))
        )
        brand = result.scalar_one_or_none()

        if not brand:
            brand = Brand(name=name)
            session.add(brand)
            await session.flush()

        return brand

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        async with get_session() as session:
            result = await session.execute(
                select(Product)
                .where(Product.id == product_id)
                .options(
                    selectinload(Product.category),
                    selectinload(Product.brand)
                )
            )
            return result.scalar_one_or_none()

    async def get_by_gtin(self, gtin: str) -> Optional[Product]:
        """
        Get product by GTIN code.

        Args:
            gtin: GTIN code

        Returns:
            Product or None if not found
        """
        async with get_session() as session:
            # Normalize GTIN to 14 digits
            normalized_gtin = gtin.zfill(14)

            from ..models.product import ProductGTIN

            result = await session.execute(
                select(ProductGTIN)
                .where(ProductGTIN.gtin == normalized_gtin)
                .options(
                    selectinload(ProductGTIN.product).selectinload(Product.category),
                    selectinload(ProductGTIN.product).selectinload(Product.brand)
                )
            )
            gtin_record = result.scalar_one_or_none()

            if gtin_record:
                return gtin_record.product

            return None

    async def search_products(
        self,
        query: str,
        limit: int = 10
    ) -> List[Product]:
        """
        Search products by name.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of matching products
        """
        async with get_session() as session:
            result = await session.execute(
                select(Product)
                .where(Product.name.ilike(f"%{query}%"))
                .options(
                    selectinload(Product.category),
                    selectinload(Product.brand)
                )
                .limit(limit)
            )
            return list(result.scalars().all())

    async def get_all_categories(self) -> List[Category]:
        """Get all product categories."""
        async with get_session() as session:
            result = await session.execute(
                select(Category).order_by(Category.id)
            )
            return list(result.scalars().all())

    async def get_all_brands(self) -> List[Brand]:
        """Get all brands."""
        async with get_session() as session:
            result = await session.execute(
                select(Brand).order_by(Brand.name)
            )
            return list(result.scalars().all())
