"""Main menu keyboard."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


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


def get_add_choose_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for choosing add method."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📷 Сканировать", callback_data="add_choose_scan"),
            InlineKeyboardButton(text="✏️ Вручную", callback_data="add_choose_manual")
        ]
    ])
