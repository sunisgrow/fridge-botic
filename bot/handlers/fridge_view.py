"""Handler for viewing and managing fridge contents."""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from ..services.api_client import APIClient
from ..keyboards.main_menu import get_main_keyboard

logger = logging.getLogger(__name__)

router = Router()

# Messages
FRIDGE_EMPTY = "🧊 Ваш холодильник пуст.\n\nДобавьте первый продукт командой /add"
FRIDGE_TITLE = "🧊 Содержимое холодильника:\n\n"
EXPIRING_WARNING = "\n⚠️ <b>Скоро истекает:</b>\n"
DELETE_CONFIRM = "🗑️ Удалить продукт?\n\n<b>{product_name}</b> × {quantity}\n\nПричина:"
DELETE_SUCCESS = "✅ Продукт удалён: {product_name}"
DELETE_CANCELLED = "❌ Удаление отменено"
NO_ITEMS_TO_DELETE = "В холодильнике нет продуктов для удаления."


@router.message(Command("fridge"))
@router.message(F.text == "📋 Холодильник")
async def show_fridge(message: Message, api_client: APIClient):
    """
    Show all products in user's fridge.
    
    Groups by category and highlights expiring items.
    """
    telegram_id = message.from_user.id

    try:
        items = await api_client.get_fridge_items(telegram_id)
    except Exception as e:
        logger.error(f"Failed to get fridge items: {e}")
        await message.answer(
            "❌ Не удалось получить содержимое холодильника",
            reply_markup=get_main_keyboard()
        )
        return

    if not items or not items.get("items"):
        await message.answer(FRIDGE_EMPTY, reply_markup=get_main_keyboard())
        return

    fridge_items = items["items"]

    # Group by category
    categories: dict[str, list] = {}
    expiring: list = []

    for item in fridge_items:
        category = item.get("category") or "Другое"
        if category not in categories:
            categories[category] = []
        categories[category].append(item)

        days = item.get("days_until_expiry")
        if days is not None and days <= 3:
            expiring.append(item)

    # Build message
    text = FRIDGE_TITLE

    for category, cat_items in categories.items():
        icon = cat_items[0].get("category_icon", "📦")
        text += f"\n<b>{icon} {category}:</b>\n"

        for item in cat_items:
            name = item.get("product_name", "Неизвестно")
            quantity = item.get("quantity", 1)
            days = item.get("days_until_expiry")

            # Format expiration
            if days is not None:
                if days < 0:
                    expiry_text = f" ❌ <b>Истёк!</b>"
                elif days == 0:
                    expiry_text = f" ⚠️ <b>Сегодня!</b>"
                elif days <= 3:
                    expiry_text = f" ⚠️ {days} дн."
                else:
                    expiry_text = f" 📅 {days} дн."
            else:
                expiry_text = ""

            text += f"  • {name} × {quantity}{expiry_text}\n"

    # Add expiring warning
    if expiring:
        text += EXPIRING_WARNING
        for item in expiring:
            name = item.get("product_name", "Неизвестно")
            days = item.get("days_until_expiry", 0)
            text += f"  • {name} - {days} дн.\n"

    # Add delete button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑️ Удалить продукты", callback_data="delete_select"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_fridge")
            ]
        ]
    )

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "refresh_fridge")
async def refresh_fridge(callback: CallbackQuery, api_client: APIClient):
    """Refresh fridge view."""
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
    await show_fridge(fake_message, api_client)
    await callback.answer()


@router.callback_query(F.data == "delete_select")
async def select_delete(callback: CallbackQuery, api_client: APIClient):
    """Show product selection for deletion."""
    telegram_id = callback.from_user.id

    try:
        items = await api_client.get_fridge_items(telegram_id)
    except Exception as e:
        logger.error(f"Failed to get fridge items: {e}")
        await callback.answer("❌ Ошибка при загрузке продуктов")
        return

    if not items or not items.get("items"):
        await callback.message.edit_text(NO_ITEMS_TO_DELETE)
        await callback.answer()
        return

    fridge_items = items["items"]

    # Create keyboard with products
    buttons = []
    for item in fridge_items[:10]:  # Limit to 10 items
        name = item.get("product_name", "Неизвестно")
        quantity = item.get("quantity", 1)
        item_id = item.get("id")

        buttons.append([
            InlineKeyboardButton(
                text=f"{name} × {quantity}",
                callback_data=f"delete_{item_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        "🗑️ Выберите продукт для удаления:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_") & ~F.data.contains("select"))
async def confirm_delete(callback: CallbackQuery):
    """Confirm product deletion."""
    item_id = int(callback.data.split("_")[1])

    # Create confirmation keyboard
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Использовано", callback_data=f"confirm_{item_id}_used"),
                InlineKeyboardButton(text="⚠️ Истекло", callback_data=f"confirm_{item_id}_expired")
            ],
            [
                InlineKeyboardButton(text="📦 Другое", callback_data=f"confirm_{item_id}_other"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")
            ]
        ]
    )

    await callback.message.edit_text(
        "🗑️ Удалить продукт?\n\nВыберите причину:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_"))
async def delete_product(callback: CallbackQuery, api_client: APIClient):
    """Delete product from fridge."""
    parts = callback.data.split("_")
    item_id = int(parts[1])
    reason = parts[2] if len(parts) > 2 else None

    telegram_id = callback.from_user.id

    try:
        await api_client.delete_fridge_item(telegram_id, item_id, reason)
        await callback.message.edit_text(
            "✅ Продукт удалён",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 К холодильнику", callback_data="refresh_fridge")]
                ]
            )
        )
        logger.info(f"Deleted item {item_id}, reason: {reason}")
    except Exception as e:
        logger.error(f"Failed to delete item: {e}")
        await callback.answer("❌ Ошибка при удалении")

    await callback.answer()


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    """Cancel deletion."""
    await callback.message.delete()
    await callback.answer(DELETE_CANCELLED)


@router.message(F.text == "🗑️ Удалить")
async def show_delete_menu(message: Message, api_client: APIClient):
    """Show product selection for deletion from main menu."""
    telegram_id = message.from_user.id

    try:
        items = await api_client.get_fridge_items(telegram_id)
    except Exception as e:
        logger.error(f"Failed to get fridge items: {e}")
        await message.answer(
            "❌ Не удалось получить список продуктов",
            reply_markup=get_main_keyboard()
        )
        return

    if not items or not items.get("items"):
        await message.answer(
            NO_ITEMS_TO_DELETE,
            reply_markup=get_main_keyboard()
        )
        return

    fridge_items = items["items"]

    # Create keyboard with products
    buttons = []
    for item in fridge_items[:10]:  # Limit to 10 items
        name = item.get("product_name", "Неизвестно")
        quantity = item.get("quantity", 1)
        item_id = item.get("id")
        days = item.get("days_until_expiry")

        # Add expiration indicator
        if days is not None:
            if days < 0:
                status = "❌"
            elif days <= 3:
                status = "⚠️"
            else:
                status = "✅"
        else:
            status = ""

        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {name} × {quantity}",
                callback_data=f"delete_{item_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete_main")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        "🗑️ Выберите продукт для удаления:",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "cancel_delete_main")
async def cancel_delete_main(callback: CallbackQuery):
    """Cancel deletion from main menu."""
    await callback.message.delete()
    await callback.answer()
