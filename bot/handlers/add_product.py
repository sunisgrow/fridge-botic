"""Handler for adding products to fridge."""

import json
import logging
from datetime import datetime, date

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from scanner.gs1_parser import parse_gs1, GS1ParseError
from ..services.api_client import APIClient
from ..keyboards.main_menu import get_main_keyboard, get_cancel_keyboard, get_cancel_inline_keyboard, get_add_choose_keyboard
from ..keyboards.categories import get_categories_keyboard
from ..keyboards.scan_keyboard import get_scan_confirm_keyboard
from ..config import settings
from .scan_product import ScanStates

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


async def process_webapp_result(message_or_callback, state: FSMContext, api_client: APIClient, scan_data: dict, is_callback: bool = False):
    """Process webapp scan result and show product info."""
    telegram_id = message_or_callback.from_user.id
    
    raw_data = scan_data.get('raw', '')
    scan_format = scan_data.get('format', '')
    
    # Parse GS1 data if format is DataMatrix
    gtin = None
    gs1_data = None
    
    if scan_format == 'DATA_MATRIX' and raw_data:
        try:
            gs1_data = parse_gs1(raw_data)
            gtin = gs1_data.get('gtin')
            logger.info(f"GS1 parsed: gtin={gtin}, serial={gs1_data.get('serial')}")
        except GS1ParseError as e:
            logger.warning(f"GS1 parse error: {e}")
    
    # If no GTIN from GS1, try raw data as EAN/UPC
    if not gtin and raw_data:
        # Clean and try as EAN/UPC
        cleaned = raw_data.strip()
        if cleaned.isdigit() and len(cleaned) >= 8:
            gtin = cleaned
    
    if not gtin:
        await message_or_callback.answer(
            "❌ Не удалось извлечь GTIN из кода. Попробуйте еще раз или введите вручную: /add",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        if is_callback:
            await message_or_callback.answer()
        return
    
    try:
        result = await api_client.lookup_product(
            telegram_id=telegram_id,
            raw_data=raw_data,
            gtin=gtin
        )
        
        logger.info(f"Scan result: {result}")
        
        if not result.get('success'):
            await message_or_callback.answer(
                f"❌ Ошибка: {result.get('message', 'Неизвестная ошибка')}",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            if is_callback:
                await message_or_callback.answer()
            return
        
        if result.get('product_name'):
            default_shelf = result.get('default_shelf_life') or 7
            exp_info = ""
            if result.get('expiration_date'):
                exp_info = f"Срок годности (из кода): {result['expiration_date']}\n"
            exp_info += f"Или будет использован срок по умолчанию: {default_shelf} дней"
            
            text = f"""📦 Найден товар:

Название: {result['product_name']}
Категория: {result.get('category_name', 'Неизвестно')}
Бренд: {result.get('brand_name', 'Неизвестно')}
GTIN: {result['gtin']}
Срок годности (по умолчанию): {default_shelf} дней

{exp_info}"""
            
            await state.update_data(scan_result=result)
            await state.set_state(ScanStates.editing_product)
            
            if is_callback:
                await message_or_callback.message.answer(text, reply_markup=get_scan_confirm_keyboard())
            else:
                await message_or_callback.answer(text, reply_markup=get_scan_confirm_keyboard())
            if is_callback:
                await message_or_callback.answer()
        else:
            await message_or_callback.answer(
                f"❌ Товар не найден в базе\n\nGTIN: {result.get('gtin', 'N/A')}",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            if is_callback:
                await message_or_callback.answer()
            
    except Exception as e:
        logger.error(f"Error processing webapp result: {e}", exc_info=True)
        await message_or_callback.answer(
            f"❌ Ошибка обработки: {str(e)}",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        if is_callback:
            await message_or_callback.answer()


@router.message(Command("add"))
@router.message(F.text == "➕ Добавить")
async def start_add_product(message: Message, state: FSMContext):
    """Show choose add method keyboard."""
    telegram_id = message.from_user.id
    
    logger.info(f"User {telegram_id} started add product")
    
    await state.clear()
    await state.set_state(ScanStates.waiting_for_photo)
    
    webapp_url = settings.API_EXTERNAL_URL + '/webapp'
    await message.answer(
        CHOOSE_ADD_METHOD,
        reply_markup=get_add_choose_keyboard(webapp_url)
    )


@router.message(F.web_app_data)
async def handle_webapp_scan(message: Message, state: FSMContext, api_client: APIClient):
    """Handle data received from WebApp Mini App via KeyboardButton."""
    telegram_id = message.from_user.id
    logger.info(f"Processing web_app_data for user {telegram_id}")
    
    try:
        scan_data = json.loads(message.web_app_data.data)
        logger.info(f"WebApp scan data: {scan_data}")
        await process_webapp_result(message, state, api_client, scan_data, is_callback=False)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse web_app_data: {message.web_app_data.data}")
        await message.answer(
            "❌ Ошибка обработки данных сканера",
            reply_markup=get_main_keyboard()
        )
        await state.clear()


@router.message(F.text == "📸 Загрузить фото")
async def add_by_photo(message: Message, state: FSMContext):
    """Start scanning via photo upload."""
    from .scan_product import SCAN_START
    
    telegram_id = message.from_user.id
    logger.info(f"User {telegram_id} chose scan via photo")
    
    await state.clear()
    await state.set_state(ScanStates.waiting_for_photo)
    
    await message.answer(SCAN_START)


@router.message(F.text == "✏️ Вручную")
async def add_manually(message: Message, state: FSMContext):
    """Start manual input."""
    telegram_id = message.from_user.id
    logger.info(f"User {telegram_id} chose manual method")
    
    await state.clear()
    await state.set_state(AddProductState.name)
    
    await message.answer(ENTER_NAME, reply_markup=get_cancel_keyboard())


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


@router.callback_query(F.data == "cancel_add")
async def cancel_add_callback(callback: CallbackQuery, state: FSMContext):
    """Cancel add product dialog via inline button."""
    await state.clear()
    await callback.message.edit_text(CANCELLED, reply_markup=None)
    await callback.message.answer("Выберите действие:", reply_markup=get_main_keyboard())
    await callback.answer()


@router.callback_query(ScanStates.editing_product, F.data == "scan_confirm")
async def confirm_scan(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Confirm and add scanned product."""
    telegram_id = callback.from_user.id
    data = await state.get_data()
    scan_result = data.get('scan_result')
    
    try:
        expiration_date = scan_result.get('expiration_date')
        if not expiration_date:
            default_shelf = scan_result.get('default_shelf_life') or 7
            expiration_date = (date.today() + __import__('datetime').timedelta(days=default_shelf)).isoformat()
        
        await api_client.add_fridge_item(
            telegram_id=telegram_id,
            product_name=scan_result['product_name'],
            category_id=scan_result.get('category_id'),
            brand_name=scan_result.get('brand_name'),
            quantity=1,
            expiration_date=expiration_date
        )
        
        await callback.message.edit_text("✅ Товар добавлен в холодильник!", reply_markup=None)
        await callback.message.answer("Выберите действие:", reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Error adding scanned product: {e}", exc_info=True)
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}", reply_markup=None)
        await callback.message.answer(reply_markup=get_main_keyboard())
    
    await callback.answer()
    await state.clear()


@router.callback_query(ScanStates.editing_product, F.data == "scan_cancel")
async def cancel_scan(callback: CallbackQuery, state: FSMContext):
    """Cancel scanning."""
    await callback.message.edit_text("❌ Сканирование отменено", reply_markup=None)
    await callback.message.answer(reply_markup=get_main_keyboard())
    await callback.answer()
    await state.clear()
