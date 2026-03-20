"""Keyboards for scan operations."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


def get_scan_webapp_keyboard(webapp_url: str = None):
    """Keyboard for opening webapp scanner."""
    url = webapp_url or "https://fridge-bot.com/webapp"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📷 Сканировать код",
            web_app=WebAppInfo(url=url)
        )]
    ])


def get_scan_confirm_keyboard():
    """Keyboard for confirming scanned product."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Добавить", callback_data="scan_confirm"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="scan_edit")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="scan_cancel")
        ]
    ])
