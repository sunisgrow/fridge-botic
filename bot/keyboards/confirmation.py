"""Confirmation keyboard."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_confirmation_keyboard(
    confirm_callback: str,
    cancel_callback: str
) -> InlineKeyboardMarkup:
    """
    Get confirmation keyboard.
    
    Args:
        confirm_callback: Callback data for confirm button
        cancel_callback: Callback data for cancel button
        
    Returns:
        Inline keyboard with confirm/cancel buttons
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=confirm_callback),
                InlineKeyboardButton(text="❌ Нет", callback_data=cancel_callback)
            ]
        ]
    )
