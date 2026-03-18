"""Handler for viewing expiring products."""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from ..services.api_client import APIClient
from ..keyboards.main_menu import get_main_keyboard

logger = logging.getLogger(__name__)

router = Router()

# Messages
NO_EXPIRING = "✅ Нет продуктов с истекающим сроком годности"
EXPIRING_TITLE = "⚠️ <b>Истекающие продукты:</b>\n\n"
EXPIRED_TITLE = "❌ <b>Просроченные продукты:</b>\n\n"


@router.message(Command("expiring"))
@router.message(F.text == "⏰ Истекающие")
async def show_expiring(message: Message, api_client: APIClient):
    """
    Show products expiring within 3 days.
    
    Groups by expiration status.
    """
    telegram_id = message.from_user.id

    try:
        # Get expiring items (within 7 days to include expired)
        items = await api_client.get_expiring_items(telegram_id, days=7)
    except Exception as e:
        logger.error(f"Failed to get expiring items: {e}")
        await message.answer(
            "❌ Не удалось получить список истекающих продуктов",
            reply_markup=get_main_keyboard()
        )
        return

    if not items or not items.get("items"):
        await message.answer(NO_EXPIRING, reply_markup=get_main_keyboard())
        return

    fridge_items = items["items"]

    # Group by expiration status
    expired = []
    expiring_soon = []

    for item in fridge_items:
        days = item.get("days_until_expiry")
        if days is not None:
            if days < 0:
                expired.append(item)
            elif days <= 3:
                expiring_soon.append(item)

    # Build message
    text = ""

    if expired:
        text += EXPIRED_TITLE
        for item in expired:
            name = item.get("product_name", "Неизвестно")
            days = item.get("days_until_expiry", 0)
            text += f"  ❌ {name} - истёк {abs(days)} дн. назад\n"

    if expiring_soon:
        text += EXPIRING_TITLE
        for item in expiring_soon:
            name = item.get("product_name", "Неизвестно")
            days = item.get("days_until_expiry", 0)
            if days == 0:
                text += f"  ⚠️ {name} - сегодня!\n"
            else:
                text += f"  ⚠️ {name} - {days} дн.\n"

    if not text:
        text = NO_EXPIRING

    # Add action buttons
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑️ Удалить просроченные", callback_data="expire_delete_all"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_expiring")
            ]
        ]
    )

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "refresh_expiring")
async def refresh_expiring(callback: CallbackQuery, api_client: APIClient):
    """Refresh expiring products view."""
    telegram_id = callback.from_user.id
    await callback.message.delete()

    # Create a fake message with correct user ID
    class FakeMessage:
        def __init__(self, original_message, user_id):
            self._original = original_message
            self.from_user = type('obj', (object,), {'id': user_id})()
        
        def __getattr__(self, name):
            return getattr(self._original, name)
        
        async def answer(self, text, **kwargs):
            return await self._original.answer(text, **kwargs)
    
    fake_message = FakeMessage(callback.message, telegram_id)
    await show_expiring(fake_message, api_client)
    await callback.answer()


@router.callback_query(F.data == "expire_delete_all")
async def delete_expired(callback: CallbackQuery, api_client: APIClient):
    """Delete all expired products."""
    telegram_id = callback.from_user.id

    try:
        # Get expired items
        items = await api_client.get_expiring_items(telegram_id, days=7)

        if not items or not items.get("items"):
            await callback.answer("Нет просроченных продуктов")
            return

        fridge_items = items["items"]
        expired_ids = [
            item["id"] for item in fridge_items
            if item.get("days_until_expiry", 0) < 0
        ]

        if not expired_ids:
            await callback.answer("Нет просроченных продуктов")
            return

        # Batch delete
        result = await api_client.batch_delete_fridge_items(
            telegram_id,
            expired_ids,
            reason="expired"
        )

        deleted_count = result.get("deleted_count", 0)

        await callback.message.edit_text(
            f"✅ Удалено {deleted_count} просроченных продуктов",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_expiring")]
                ]
            )
        )

        logger.info(f"Deleted {deleted_count} expired items for user {telegram_id}")

    except Exception as e:
        logger.error(f"Failed to delete expired items: {e}")
        await callback.answer("❌ Ошибка при удалении")

    await callback.answer()
