"""Database session management."""

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from ..config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG if hasattr(settings, 'DEBUG') else False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.

    Usage:
        async with get_session() as session:
            result = await session.execute(query)
    """
    session = async_session_maker()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        await session.close()


async def init_db():
    """Initialize database tables."""
    from ..database.base import Base
    from ..models.category import Category

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created")

    await _load_default_categories()


async def _load_default_categories():
    """Load default categories if database is empty."""
    from ..models.category import Category

    async with async_session_maker() as session:
        result = await session.execute(select(Category).limit(1))
        if result.scalar_one_or_none():
            logger.info("Categories already exist, skipping load")
            return

    data_dir = Path(__file__).parent.parent.parent / "data"
    categories_file = data_dir / "categories.json"

    if not categories_file.exists():
        logger.warning(f"Categories file not found: {categories_file}")
        return

    with open(categories_file, 'r', encoding='utf-8') as f:
        categories = json.load(f)

    async with async_session_maker() as session:
        for cat_data in categories:
            result = await session.execute(
                select(Category).where(Category.id == cat_data['id'])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                category = Category(
                    id=cat_data['id'],
                    name=cat_data['name'],
                    icon=cat_data.get('icon')
                )
                session.add(category)
                logger.info(f"Added category: {cat_data['name']}")

        await session.commit()

    logger.info(f"Loaded {len(categories)} default categories")


async def close_db():
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
