"""Handler for adding products to fridge."""

import logging
from datetime import datetime, date

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..services.api_client import APIClient
from ..keyboards.main_menu import get_main_keyboard, get_cancel_keyboard, get_add_choose_keyboard
from ..keyboards.categories import get_categories_keyboard

logger = logging.getLogger(__name__)

router = Router()


class AddProductState(StatesGroup):
    """FSM states for adding product."""
    name = State()
    category = State()
    quantity = State()
    expiration = State()


CHOOSE_ADD_METHOD = "Выберите способ добавления продукта:"

# Messages
ENTER_NAME = "📦 Введите название продукта:"
ENTER_QUANTITY = "🔢 Введите количество (по умолчанию 1):"
ENTER_EXPIRATION = """📅 Введите срок годности:
• В формате ДД.ММ.ГГГГ (например: 25.12.2024)
• Или количество дней (например: 7)
• Или пропустите, нажав /skip"""
CHOOSE_CATEGORY = "📂 Выберите категорию:"
PRODUCT_ADDED = "✅ Продукт добавлен в холодильник!"
CANCELLED = "❌ Добавление отменено"


@router.message(Command("add"))
@router.message(F.text == "➕ Добавить")
async def start_add_product(message: Message, state: FSMContext):
    """Show choose add method keyboard."""
    telegram_id = message.from_user.id
    
    logger.info(f"User {telegram_id} started add product")
    
    # Reset state
    await state.clear()
    
    # Show choose method keyboard
    await message.answer(
        CHOOSE_ADD_METHOD,
        reply_markup=get_add_choose_keyboard()
    )


@router.callback_query(F.data == "add_choose_scan")
async def add_by_scan(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Start scanning to add product."""
    telegram_id = callback.from_user.id
    logger.info(f"User {telegram_id} chose scan method")
    
    # Clear state and set scanning state
    await state.clear()
    
    # Import here to avoid circular import
    from .scan_product import ScanStates, SCAN_START
    
    await state.set_state(ScanStates.waiting_for_photo)
    
    await callback.message.edit_text(SCAN_START)
    await callback.answer()


@router.callback_query(F.data == "add_choose_manual")
async def add_manually(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Start manual input."""
    telegram_id = callback.from_user.id
    logger.info(f"User {telegram_id} chose manual method")
    
    # Clear state and set add state
    await state.clear()
    await state.set_state(AddProductState.name)
    
    await callback.message.edit_text(ENTER_NAME, reply_markup=get_cancel_keyboard())
    await callback.answer()


@router.message(AddProductState.name)
async def process_name(message: Message, state: FSMContext, api_client: APIClient):
    """Process product name."""
    name = message.text.strip()
    
    if len(name) < 1 or len(name) > 255:
        await message.answer("❌ Название должно быть от 1 до 255 символов")
        return
    
    # Save name
    await state.update_data(product_name=name)
    
    # Ask category
    await state.set_state(AddProductState.category)
    
    try:
        # Get categories from API
        categories = await api_client.get_categories()
        keyboard = get_categories_keyboard(categories)
        await message.answer(CHOOSE_CATEGORY, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        # Skip category selection
        await state.set_state(AddProductState.quantity)
        await message.answer(ENTER_QUANTITY, reply_markup=get_cancel_keyboard())


@router.callback_query(AddProductState.category, F.data.startswith("cat_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    """Process category selection."""
    category_id = int(callback.data.split("_")[1])
    
    # Save category
    await state.update_data(category_id=category_id)
    
    # Ask quantity
    await state.set_state(AddProductState.quantity)
    
    await callback.message.answer(ENTER_QUANTITY, reply_markup=get_cancel_keyboard())
    await callback.answer()


@router.callback_query(AddProductState.category, F.data == "skip_category")
async def skip_category(callback: CallbackQuery, state: FSMContext):
    """Skip category selection."""
    # Ask quantity
    await state.set_state(AddProductState.quantity)
    
    await callback.message.answer(ENTER_QUANTITY, reply_markup=get_cancel_keyboard())
    await callback.answer()


@router.message(AddProductState.quantity)
async def process_quantity(message: Message, state: FSMContext):
    """Process quantity."""
    text = message.text.strip()
    
    try:
        quantity = int(text)
        if quantity < 1 or quantity > 1000:
            raise ValueError("Quantity out of range")
    except ValueError:
        await message.answer("❌ Введите число от 1 до 1000")
        return
    
    # Save quantity
    await state.update_data(quantity=quantity)
    
    # Ask expiration date
    await state.set_state(AddProductState.expiration)
    
    await message.answer(ENTER_EXPIRATION, reply_markup=get_cancel_keyboard())


@router.message(AddProductState.expiration)
async def process_expiration(message: Message, state: FSMContext, api_client: APIClient):
    """Process expiration date and save product."""
    text = message.text.strip()
    expiration_date = None
    
    if text != "/skip":
        try:
            # Try DD.MM.YYYY format
            if "." in text:
                expiration_date = datetime.strptime(text, "%d.%m.%Y").date()
            else:
                # Try days
                days = int(text)
                if days < 1 or days > 365:
                    raise ValueError("Days out of range")
                expiration_date = date.today() + __import__('datetime').timedelta(days=days)
        except ValueError:
            await message.answer("❌ Неверный формат. Используйте ДД.ММ.ГГГГ или количество дней")
            return
    
    # Get saved data
    data = await state.get_data()
    
    try:
        # Add product to fridge
        await api_client.add_fridge_item(
            telegram_id=message.from_user.id,
            product_name=data["product_name"],
            category_id=data.get("category_id"),
            quantity=data["quantity"],
            expiration_date=expiration_date.isoformat() if expiration_date else None
        )
        
        await message.answer(PRODUCT_ADDED, reply_markup=get_main_keyboard())
        logger.info(f"Product added: {data['product_name']}")
        
    except Exception as e:
        logger.error(f"Failed to add product: {e}")
        await message.answer(
            f"❌ Ошибка при добавлении продукта: {str(e)}",
            reply_markup=get_main_keyboard()
        )
    
    # Clear state
    await state.clear()


@router.message(F.text == "❌ Отмена")
async def cancel_add(message: Message, state: FSMContext):
    """Cancel add product dialog."""
    await state.clear()
    await message.answer(CANCELLED, reply_markup=get_main_keyboard())
