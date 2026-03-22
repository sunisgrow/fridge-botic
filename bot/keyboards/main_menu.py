"""Main menu keyboard."""

from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    buttons = [
        [
            KeyboardButton(text="➕ Добавить"),
            KeyboardButton(text="📋 Холодильник")
        ],
        [
            KeyboardButton(text="⏰ Истекающие"),
            KeyboardButton(text="🗑️ Удалить")
        ],
        [
            KeyboardButton(text="📖 Рецепты"),
            KeyboardButton(text="🛒 Покупки")
        ],
        [
            KeyboardButton(text="⚙️ Настройки"),
            KeyboardButton(text="❓ Помощь")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard with cancel button."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


def get_cancel_inline_keyboard() -> InlineKeyboardMarkup:
    """Get inline keyboard with cancel button (for edit_text)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add")]
    ])


def get_add_choose_keyboard(webapp_url: Optional[str] = None) -> ReplyKeyboardMarkup:
    """Keyboard for choosing add method."""
    url = webapp_url or "https://fridge-bot.com/webapp"
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📷 Сканировать код", web_app=WebAppInfo(url=url))],
        [KeyboardButton(text="📸 Загрузить фото")],
        [KeyboardButton(text="✏️ Вручную")],
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)
