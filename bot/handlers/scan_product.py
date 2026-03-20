"""Handler for scanning products via DataMatrix."""

import json
import logging
from datetime import date, timedelta, datetime
from io import BytesIO

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..services.api_client import APIClient
from ..keyboards.main_menu import get_main_keyboard
from ..keyboards.scan_keyboard import get_scan_confirm_keyboard

logger = logging.getLogger(__name__)

router = Router()


class ScanStates(StatesGroup):
    """FSM states for scanning."""
    waiting_for_photo = State()
    editing_product = State()
    waiting_quantity = State()
    waiting_expiration = State()


SCAN_START = """📷 Отправьте фото DataMatrix кода с упаковки товара

Код обычно находится на упаковке в виде квадратного кода с точками 🇷🇺"""

SCAN_PROCESSING = "⏳ Сканирую..."

PRODUCT_FOUND = """📦 Найден товар:

Название: {product_name}
Категория: {category}
Бренд: {brand}
GTIN: {gtin}
Срок годности (по умолчанию): {shelf_life} дней

{expiration_info}
"""

PRODUCT_NOT_FOUND = """❌ Товар не найден в базе

GTIN: {gtin}
 raw_data: {raw_data}

Вы можете добавить товар вручную: /add"""

PRODUCT_SCAN_ERROR = """❌ Ошибка сканирования

{error}

Попробуйте еще раз или добавьте товар вручную: /add"""

PRODUCT_ADDED = "✅ Товар добавлен в холодильник!"

SCAN_CANCELLED = "❌ Сканирование отменено"

ENTER_QUANTITY = "🔢 Введите количество (по умолчанию 1):"

ENTER_EXPIRATION = """📅 Введите срок годности:
• В формате ДД.ММ.ГГГГ (например: 25.12.2024)
• Или количество дней (например: 7)
• Или пропустите, нажав /skip"""


@router.message(Command("scan"))
@router.message(F.text == "📷 Сканировать")
async def start_scan(message: Message, state: FSMContext):
    """Start scanning process."""
    logger.info(f"User {message.from_user.id} started scan")
    
    await state.clear()
    await state.set_state(ScanStates.waiting_for_photo)
    
    await message.answer(SCAN_START)


@router.callback_query()
async def process_webapp_data(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Process data received from WebApp Mini App via callback_query."""
    telegram_id = callback.from_user.id
    logger.info(f"Callback received: data={callback.data}, web_app_data={callback.web_app_data}")
    
    if not callback.data:
        await callback.answer()
        return
    
    try:
        import json
        webapp_data = json.loads(callback.data)
        
        logger.info(f"WebApp scan data: {webapp_data}")
        
        processing_msg = await callback.message.answer(SCAN_PROCESSING)
        
        raw_data = webapp_data.get('raw', '')
        gtin = webapp_data.get('gtin')
        
        if not gtin:
            await processing_msg.delete()
            await callback.message.answer(
                "❌ Не удалось извлечь GTIN из кода. Попробуйте еще раз или введите вручную: /add",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            await callback.answer()
            return
        
        result = await api_client.lookup_product(
            telegram_id=telegram_id,
            raw_data=raw_data,
            gtin=gtin
        )
        
        logger.info(f"Scan result: {result}")
        
        if not result.get('success'):
            await processing_msg.delete()
            await callback.message.answer(
                PRODUCT_SCAN_ERROR.format(error=result.get('message', 'Unknown error')),
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            await callback.answer()
            return
        
        if result.get('product_name'):
            default_shelf = result.get('default_shelf_life') or 7
            exp_info = ""
            if result.get('expiration_date'):
                exp_info = f"Срок годности (из кода): {result['expiration_date']}\n"
            exp_info += f"Или будет использован срок по умолчанию: {default_shelf} дней"
            
            text = PRODUCT_FOUND.format(
                product_name=result['product_name'],
                category=result.get('category_name', 'Неизвестно'),
                brand=result.get('brand_name', 'Неизвестно'),
                gtin=result['gtin'],
                shelf_life=default_shelf,
                expiration_info=exp_info
            )
            
            await state.update_data(scan_result=result)
            
            await processing_msg.delete()
            await callback.message.answer(text, reply_markup=get_scan_confirm_keyboard())
            await state.set_state(ScanStates.editing_product)
            
        else:
            await processing_msg.delete()
            await callback.message.answer(
                PRODUCT_NOT_FOUND.format(
                    gtin=result.get('gtin', 'N/A'),
                    raw_data=result.get('raw_data', 'N/A')
                ),
                reply_markup=get_main_keyboard()
            )
            await state.clear()
        
        await callback.answer()
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from webapp: {e}")
        await callback.message.answer(
            PRODUCT_SCAN_ERROR.format(error="Invalid data received"),
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        await callback.answer()
    except Exception as e:
        logger.error(f"Error processing webapp data: {e}", exc_info=True)
        await callback.message.answer(
            PRODUCT_SCAN_ERROR.format(error=str(e)),
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        await callback.answer()


@router.message(ScanStates.waiting_for_photo, F.content_type == "photo")
async def process_scan_photo(message: Message, state: FSMContext, api_client: APIClient):
    """Process received photo with DataMatrix code."""
    telegram_id = message.from_user.id
    logger.info(f"Processing scan photo for user {telegram_id}")
    
    # Show processing message
    processing_msg = await message.answer(SCAN_PROCESSING)
    
    try:
        # Get the largest photo
        photo = message.photo[-1]
        
        # Download photo
        file = await message.bot.get_file(photo.file_id)
        file_bytes = await message.bot.download_file(file.file_path)
        
        # Call API to scan
        result = await api_client.scan_datamatrix(
            telegram_id=telegram_id,
            file_bytes=file_bytes.getvalue(),
            filename=f"{telegram_id}.jpg"
        )
        
        logger.info(f"Scan result: {result}")
        
        if not result.get('success'):
            await processing_msg.delete()
            await message.answer(
                PRODUCT_SCAN_ERROR.format(error=result.get('message', 'Unknown error')),
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return
        
        # Check if product was found
        if result.get('product_name'):
            # Build expiration info
            default_shelf = result.get('default_shelf_life') or 7
            exp_info = ""
            if result.get('expiration_date'):
                exp_info = f"Срок годности (из кода): {result['expiration_date']}\n"
            exp_info += f"Или будет использован срок по умолчанию: {default_shelf} дней"
            
            # Show product info with confirm keyboard
            text = PRODUCT_FOUND.format(
                product_name=result['product_name'],
                category=result.get('category_name', 'Неизвестно'),
                brand=result.get('brand_name', 'Неизвестно'),
                gtin=result['gtin'],
                shelf_life=default_shelf,
                expiration_info=exp_info
            )
            
            # Store scan result in state
            await state.update_data(scan_result=result)
            
            await processing_msg.delete()
            await message.answer(text, reply_markup=get_scan_confirm_keyboard())
            await state.set_state(ScanStates.editing_product)
            
        else:
            # Product not found
            await processing_msg.delete()
            await message.answer(
                PRODUCT_NOT_FOUND.format(
                    gtin=result.get('gtin', 'N/A'),
                    raw_data=result.get('raw_data', 'N/A')
                ),
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            
    except Exception as e:
        logger.error(f"Error processing scan: {e}", exc_info=True)
        await processing_msg.delete()
        await message.answer(
            PRODUCT_SCAN_ERROR.format(error=str(e)),
            reply_markup=get_main_keyboard()
        )
        await state.clear()


@router.message(ScanStates.waiting_for_photo)
async def wrong_content_type(message: Message):
    """Handle non-photo content."""
    await message.answer(
        "📷 Пожалуйста, отправьте фото DataMatrix кода",
        reply_markup=get_main_keyboard()
    )


@router.callback_query(ScanStates.editing_product, F.data == "scan_confirm")
async def confirm_scan(callback: CallbackQuery, state: FSMContext, api_client: APIClient):
    """Confirm and add scanned product."""
    telegram_id = callback.from_user.id
    data = await state.get_data()
    scan_result = data.get('scan_result')
    
    try:
        # Get expiration date (default or from scan)
        expiration_date = scan_result.get('expiration_date')
        if not expiration_date:
            default_shelf = scan_result.get('default_shelf_life') or 7
            expiration_date = (date.today() + timedelta(days=default_shelf)).isoformat()
        
        # Add to fridge
        await api_client.add_fridge_item(
            telegram_id=telegram_id,
            product_name=scan_result['product_name'],
            category_id=scan_result.get('category_id'),
            brand_name=scan_result.get('brand_name'),
            quantity=1,
            expiration_date=expiration_date
        )
        
        await callback.message.edit_text(PRODUCT_ADDED, reply_markup=None)
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error adding scanned product: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ Ошибка при добавлении: {str(e)}",
            reply_markup=None
        )
        await callback.message.answer(reply_markup=get_main_keyboard())
    
    await callback.answer()
    await state.clear()


@router.callback_query(ScanStates.editing_product, F.data == "scan_edit")
async def edit_scan(callback: CallbackQuery, state: FSMContext):
    """Edit scanned product before adding."""
    await state.set_state(ScanStates.waiting_quantity)
    await callback.message.answer(ENTER_QUANTITY)
    await callback.answer()


@router.callback_query(ScanStates.editing_product, F.data == "scan_cancel")
async def cancel_scan(callback: CallbackQuery, state: FSMContext):
    """Cancel scanning."""
    await callback.message.edit_text(SCAN_CANCELLED)
    await callback.message.answer(reply_markup=get_main_keyboard())
    await callback.answer()
    await state.clear()


@router.message(ScanStates.waiting_quantity)
async def process_quantity(message: Message, state: FSMContext, api_client: APIClient):
    """Process quantity input."""
    text = message.text.strip()
    
    try:
        quantity = int(text)
        if quantity < 1 or quantity > 1000:
            raise ValueError("Quantity out of range")
    except ValueError:
        await message.answer("❌ Введите число от 1 до 1000")
        return
    
    await state.update_data(quantity=quantity)
    await state.set_state(ScanStates.waiting_expiration)
    await message.answer(ENTER_EXPIRATION)


@router.message(ScanStates.waiting_expiration)
async def process_expiration_and_add(
    message: Message,
    state: FSMContext,
    api_client: APIClient
):
    """Process expiration date and add product."""
    telegram_id = message.from_user.id
    text = message.text.strip()
    
    data = await state.get_data()
    scan_result = data.get('scan_result')
    quantity = data.get('quantity', 1)
    
    # Calculate expiration date
    expiration_date = None
    if text != "/skip":
        try:
            if "." in text:
                expiration_date = datetime.strptime(text, "%d.%m.%Y").date().isoformat()
            else:
                days = int(text)
                if 1 <= days <= 365:
                    expiration_date = (date.today() + timedelta(days=days)).isoformat()
        except ValueError:
            pass
    
    # Use default if not provided
    if not expiration_date:
        default_shelf = scan_result.get('default_shelf_life') or 7
        expiration_date = (date.today() + timedelta(days=default_shelf)).isoformat()
    
    try:
        await api_client.add_fridge_item(
            telegram_id=telegram_id,
            product_name=scan_result['product_name'],
            category_id=scan_result.get('category_id'),
            brand_name=scan_result.get('brand_name'),
            quantity=quantity,
            expiration_date=expiration_date
        )
        
        await message.answer(PRODUCT_ADDED, reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Error adding scanned product: {e}", exc_info=True)
        await message.answer(
            f"❌ Ошибка при добавлении: {str(e)}",
            reply_markup=get_main_keyboard()
        )
    
    await state.clear()
