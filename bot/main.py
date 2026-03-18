"""
Telegram bot for Fridge management.

Features:
- Add products to fridge
- View fridge contents
- Get expiration notifications
- Delete products
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from .config import settings
from .handlers import start, add_product, fridge_view, expiring_products, settings as settings_handler
from .handlers.scan_product import router as scan_router
from .services.api_client import APIClient

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for bot."""
    logger.info("Starting Fridge Bot...")

    # Initialize bot
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Initialize storage
    try:
        storage = RedisStorage.from_url(settings.REDIS_URL)
        logger.info("Using Redis storage for FSM")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Using memory storage")
        storage = MemoryStorage()

    # Initialize dispatcher
    dp = Dispatcher(storage=storage)

    # Initialize API client
    api_client = APIClient(settings.API_URL)

    # Register handlers
    dp.include_router(start.router)
    dp.include_router(add_product.router)
    dp.include_router(fridge_view.router)
    dp.include_router(expiring_products.router)
    dp.include_router(settings_handler.router)
    dp.include_router(scan_router)

    # Register API client as dependency
    dp["api_client"] = api_client

    logger.info("Bot started successfully")

    try:
        # Start polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Cleanup
        await api_client.close()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
