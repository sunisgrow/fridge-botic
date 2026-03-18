"""Categories keyboard."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_categories_keyboard(categories: list[dict]) -> InlineKeyboardMarkup:
    """
    Get inline keyboard with categories.
    
    Args:
        categories: List of category dicts with id, name, icon
        
    Returns:
        Inline keyboard with category buttons
    """
    buttons = []
    
    # Add categories in rows of 2
    row = []
    for i, cat in enumerate(categories):
        icon = cat.get("icon", "📦")
        name = cat.get("name", "Другое")
        cat_id = cat.get("id")
        
        row.append(
            InlineKeyboardButton(
                text=f"{icon} {name}",
                callback_data=f"cat_{cat_id}"
            )
        )
        
        # New row every 2 buttons
        if len(row) == 2 or i == len(categories) - 1:
            buttons.append(row)
            row = []
    
    # Add skip button
    buttons.append([
        InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_category")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
