"""Handler for notification settings."""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from ..services.api_client import APIClient
from ..keyboards.main_menu import get_main_keyboard

logger = logging.getLogger(__name__)

router = Router()

# Messages
SETTINGS_TITLE = """⚙️ Настройки уведомлений

Текущие настройки:
• Уведомления: {enabled}
• За {days} дней до истечения
• Время: {time}

Выберите действие:"""

NOTIFICATION_UPDATED = "✅ Настройки обновлены"


@router.message(Command("settings"))
@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message, api_client: APIClient):
    """Show notification settings."""
    telegram_id = message.from_user.id

    try:
        settings = await api_client.get_notification_settings(telegram_id)
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        settings = {
            "enabled": True,
            "days_before": 3,
            "notify_time": "09:00"
        }

    # Format settings
    enabled = "✅ Включены" if settings.get("enabled") else "❌ Выключены"
    days = settings.get("days_before", 3)
    time = settings.get("notify_time", "09:00")

    text = SETTINGS_TITLE.format(
        enabled=enabled,
        days=days,
        time=time
    )

    # Create keyboard
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔔 Включить" if not settings.get("enabled") else "🔕 Выключить",
                    callback_data="toggle_notifications"
                )
            ],
            [
                InlineKeyboardButton(text="📅 За 1 день", callback_data="days_1"),
                InlineKeyboardButton(text="📅 За 3 дня", callback_data="days_3"),
                InlineKeyboardButton(text="📅 За 7 дней", callback_data="days_7")
            ],
            [
                InlineKeyboardButton(text="🕘 Утро (09:00)", callback_data="time_09:00"),
                InlineKeyboardButton(text="🕐 День (12:00)", callback_data="time_12:00"),
                InlineKeyboardButton(text="🕕 Вечер (18:00)", callback_data="time_18:00")
            ]
        ]
    )

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(callback: CallbackQuery, api_client: APIClient):
    """Toggle notifications on/off."""
    telegram_id = callback.from_user.id

    try:
        # Get current settings
        settings = await api_client.get_notification_settings(telegram_id)
        current_enabled = settings.get("enabled", True)

        # Toggle
        await api_client.update_notification_settings(
            telegram_id,
            enabled=not current_enabled
        )

        await callback.answer(NOTIFICATION_UPDATED)

        # Refresh settings view with correct user ID
        await callback.message.delete()
        
        # Create fake message with correct user ID
        class FakeMessage:
            def __init__(self, original_message, user_id):
                self._original = original_message
                self.from_user = type('obj', (object,), {'id': user_id})()
            
            def __getattr__(self, name):
                return getattr(self._original, name)
            
            async def answer(self, text, **kwargs):
                return await self._original.answer(text, **kwargs)
        
        fake_message = FakeMessage(callback.message, telegram_id)
        await show_settings(fake_message, api_client)

    except Exception as e:
        logger.error(f"Failed to toggle notifications: {e}")
        await callback.answer("❌ Ошибка при обновлении настроек")

    await callback.answer()


@router.callback_query(F.data.startswith("days_"))
async def set_days_before(callback: CallbackQuery, api_client: APIClient):
    """Set days before expiration to notify."""
    telegram_id = callback.from_user.id
    days = int(callback.data.split("_")[1])

    try:
        await api_client.update_notification_settings(
            telegram_id,
            days_before=days
        )

        await callback.answer(f"✅ Уведомления за {days} дней")

        # Refresh settings view with correct user ID
        await callback.message.delete()
        
        # Create fake message with correct user ID
        class FakeMessage:
            def __init__(self, original_message, user_id):
                self._original = original_message
                self.from_user = type('obj', (object,), {'id': user_id})()
            
            def __getattr__(self, name):
                return getattr(self._original, name)
            
            async def answer(self, text, **kwargs):
                return await self._original.answer(text, **kwargs)
        
        fake_message = FakeMessage(callback.message, telegram_id)
        await show_settings(fake_message, api_client)

    except Exception as e:
        logger.error(f"Failed to update days: {e}")
        await callback.answer("❌ Ошибка при обновлении настроек")

    await callback.answer()


@router.callback_query(F.data.startswith("time_"))
async def set_notify_time(callback: CallbackQuery, api_client: APIClient):
    """Set notification time."""
    telegram_id = callback.from_user.id
    time = callback.data.split("_")[1]

    try:
        await api_client.update_notification_settings(
            telegram_id,
            notify_time=time
        )

        await callback.answer(f"✅ Время уведомлений: {time}")

        # Refresh settings view with correct user ID
        await callback.message.delete()
        
        # Create fake message with correct user ID
        class FakeMessage:
            def __init__(self, original_message, user_id):
                self._original = original_message
                self.from_user = type('obj', (object,), {'id': user_id})()
            
            def __getattr__(self, name):
                return getattr(self._original, name)
            
            async def answer(self, text, **kwargs):
                return await self._original.answer(text, **kwargs)
        
        fake_message = FakeMessage(callback.message, telegram_id)
        await show_settings(fake_message, api_client)

    except Exception as e:
        logger.error(f"Failed to update time: {e}")
        await callback.answer("❌ Ошибка при обновлении настроек")

    await callback.answer()
