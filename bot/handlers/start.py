"""Handler for /start command."""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from ..services.api_client import APIClient
from ..keyboards.main_menu import get_main_keyboard

logger = logging.getLogger(__name__)

router = Router()

# Messages
WELCOME_MESSAGE = """
🧊 Добро пожаловать в Fridge Bot!

Я помогу вам:
• 📦 Добавлять продукты в холодильник
• 📋 Следить за сроками годности
• ⏰ Получать уведомления об истекающих продуктах
• 🗑️ Удалять использованные продукты

Выберите действие в меню ниже:
"""

HELP_MESSAGE = """
📖 Доступные команды:

/start - Начать работу
/add - Добавить продукт
/fridge - Посмотреть холодильник
/expiring - Истекающие продукты
/scan -	Сканировать DataMatrix
/settings - Настройки уведомлений
/help - Справка
"""


@router.message(CommandStart())
async def cmd_start(message: Message, api_client: APIClient):
    """
    Handle /start command.
    
    Register user and show main menu.
    """
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    logger.info(f"Start command from user {telegram_id}")

    try:
        # Register user
        await api_client.register_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name
        )
        logger.info(f"User {telegram_id} registered successfully")
    except Exception as e:
        logger.error(f"Failed to register user: {e}")
        # Continue anyway - user might already exist

    # Send welcome message
    await message.answer(
        WELCOME_MESSAGE,
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "❓ Помощь")
@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle help command."""
    await message.answer(HELP_MESSAGE)
