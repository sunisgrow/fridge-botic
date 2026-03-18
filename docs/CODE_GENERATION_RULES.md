# Code Generation Rules

Строгие правила и стандарты для автоматической генерации кода проекта Fridge Bot.

---

## Общие принципы

### 1. Язык и локализация

**Код:** Английский
**Комментарии:** Английский
**Сообщения бота:** Русский
**Документация:** Русский (Markdown файлы)

**Пример:**

```python
# Good
async def get_expiring_products(days: int) -> list[FridgeItem]:
    """Return products expiring within specified days."""
    pass

# Bad
async def poluchit_istekayushchie_produkty(dni: int):
    pass
```

**Bot messages:**

```python
WELCOME_MESSAGE = "Добро пожаловать в Fridge Bot!"
EXPIRING_MESSAGE = "У вас есть продукты с истекающим сроком:"
```

---

### 2. Асинхронность

**Правило:** Весь I/O код должен быть async.

**Библиотеки:**
- Database: SQLAlchemy async
- HTTP: httpx / aiohttp
- Telegram: aiogram

**Пример:**

```python
# Good
async def get_user(telegram_id: int) -> User | None:
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

# Bad
def get_user(telegram_id: int) -> User | None:
    # Synchronous database call
    pass
```

---

### 3. Типизация

**Правило:** Все функции должны иметь type hints.

**Пример:**

```python
# Good
async def add_fridge_item(
    fridge_id: int,
    product_id: int,
    quantity: int = 1,
    expiration_date: date | None = None
) -> FridgeItem:
    pass

# Bad
async def add_fridge_item(fridge_id, product_id, quantity=1, expiration_date=None):
    pass
```

**Типы Pydantic:**

```python
from pydantic import BaseModel
from datetime import date

class FridgeItemCreate(BaseModel):
    product_name: str
    category_id: int
    quantity: int = 1
    expiration_date: date | None = None

class FridgeItemResponse(BaseModel):
    id: int
    product_name: str
    category: str
    quantity: int
    expiration_date: date | None
    days_until_expiry: int | None
```

---

## Структура модулей

### API Router

**Шаблон:**

```python
# api/routers/fridge.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..schemas.fridge_schema import (
    FridgeItemCreate,
    FridgeItemResponse
)
from ..services.fridge_service import FridgeService
from ..repositories.fridge_repo import FridgeRepository

router = APIRouter(prefix="/fridge", tags=["fridge"])

@router.get("/items", response_model=List[FridgeItemResponse])
async def get_fridge_items(
    telegram_id: int,
    service: FridgeService = Depends()
) -> List[FridgeItemResponse]:
    """
    Get all items in user's fridge.
    
    Args:
        telegram_id: User's Telegram ID
        
    Returns:
        List of fridge items with product details
    """
    items = await service.get_user_fridge_items(telegram_id)
    return items

@router.post("/items", response_model=FridgeItemResponse, status_code=201)
async def add_fridge_item(
    data: FridgeItemCreate,
    telegram_id: int,
    service: FridgeService = Depends()
) -> FridgeItemResponse:
    """
    Add new item to fridge.
    
    Args:
        data: Item data including product and expiration
        telegram_id: User's Telegram ID
        
    Returns:
        Created fridge item
        
    Raises:
        HTTPException: If product not found or validation fails
    """
    try:
        item = await service.add_item(telegram_id, data)
        return item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Service Layer

**Шаблон:**

```python
# api/services/fridge_service.py

from typing import List
from datetime import date, timedelta

from ..repositories.fridge_repo import FridgeRepository
from ..repositories.product_repo import ProductRepository
from ..repositories.user_repo import UserRepository
from ..schemas.fridge_schema import FridgeItemCreate, FridgeItemResponse

class FridgeService:
    """
    Business logic for fridge management.
    
    Responsibilities:
    - Manage fridge items
    - Calculate expiration warnings
    - Handle product matching
    """
    
    def __init__(
        self,
        fridge_repo: FridgeRepository,
        product_repo: ProductRepository,
        user_repo: UserRepository
    ):
        self._fridge_repo = fridge_repo
        self._product_repo = product_repo
        self._user_repo = user_repo
    
    async def get_user_fridge_items(
        self,
        telegram_id: int
    ) -> List[FridgeItemResponse]:
        """
        Get all items in user's fridge with calculated days until expiry.
        """
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("User not found")
        
        items = await self._fridge_repo.get_fridge_items(user.fridge_id)
        
        return [
            FridgeItemResponse(
                id=item.id,
                product_name=item.product.name,
                category=item.product.category.name,
                quantity=item.quantity,
                expiration_date=item.expiration_date,
                days_until_expiry=self._calculate_days_until_expiry(item.expiration_date)
            )
            for item in items
        ]
    
    async def add_item(
        self,
        telegram_id: int,
        data: FridgeItemCreate
    ) -> FridgeItemResponse:
        """
        Add new item to fridge.
        
        Flow:
        1. Find or create product
        2. Create fridge item
        3. Return response
        """
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("User not found")
        
        product = await self._product_repo.find_or_create(
            name=data.product_name,
            category_id=data.category_id
        )
        
        item = await self._fridge_repo.create_item(
            fridge_id=user.fridge_id,
            product_id=product.id,
            quantity=data.quantity,
            expiration_date=data.expiration_date
        )
        
        return FridgeItemResponse(
            id=item.id,
            product_name=product.name,
            category=product.category.name,
            quantity=item.quantity,
            expiration_date=item.expiration_date,
            days_until_expiry=self._calculate_days_until_expiry(item.expiration_date)
        )
    
    @staticmethod
    def _calculate_days_until_expiry(expiration_date: date | None) -> int | None:
        """Calculate days until expiration."""
        if not expiration_date:
            return None
        delta = expiration_date - date.today()
        return delta.days
```

### Repository Layer

**Шаблон:**

```python
# api/repositories/fridge_repo.py

from typing import List
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.fridge import Fridge, FridgeItem
from ..models.product import Product
from ..database.session import get_session

class FridgeRepository:
    """
    Data access layer for fridge operations.
    
    All database operations for fridge items.
    """
    
    async def get_fridge_items(self, fridge_id: int) -> List[FridgeItem]:
        """Get all items in a fridge with product relations."""
        async with get_session() as session:
            result = await session.execute(
                select(FridgeItem)
                .where(FridgeItem.fridge_id == fridge_id)
                .options(
                    selectinload(FridgeItem.product)
                    .selectinload(Product.category)
                )
            )
            return list(result.scalars().all())
    
    async def create_item(
        self,
        fridge_id: int,
        product_id: int,
        quantity: int,
        expiration_date: date | None
    ) -> FridgeItem:
        """Create new fridge item."""
        async with get_session() as session:
            item = FridgeItem(
                fridge_id=fridge_id,
                product_id=product_id,
                quantity=quantity,
                expiration_date=expiration_date
            )
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return item
    
    async def delete_item(self, item_id: int) -> bool:
        """Delete fridge item by ID."""
        async with get_session() as session:
            result = await session.execute(
                select(FridgeItem).where(FridgeItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            if item:
                await session.delete(item)
                await session.commit()
                return True
            return False
    
    async def get_expiring_items(
        self,
        fridge_id: int,
        days: int
    ) -> List[FridgeItem]:
        """Get items expiring within specified days."""
        target_date = date.today() + timedelta(days=days)
        async with get_session() as session:
            result = await session.execute(
                select(FridgeItem)
                .where(
                    FridgeItem.fridge_id == fridge_id,
                    FridgeItem.expiration_date <= target_date,
                    FridgeItem.expiration_date >= date.today()
                )
            )
            return list(result.scalars().all())
```

### Bot Handler

**Шаблон:**

```python
# bot/handlers/fridge_view.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ..keyboards.main_menu import get_main_keyboard
from ..keyboards.fridge import get_fridge_keyboard
from ..services.api_client import APIClient

router = Router()

# Messages
FRIDGE_EMPTY = "Ваш холодильник пуст. Добавьте первый продукт!"
FRIDGE_TITLE = "🧊 Содержимое холодильника:\n\n"
EXPIRING_WARNING = "\n⚠️ <b>Истекает срок годности:</b>\n"

@router.message(Command("fridge"))
async def show_fridge(message: Message, api_client: APIClient):
    """
    Show all products in user's fridge.
    
    Groups by category and highlights expiring items.
    """
    telegram_id = message.from_user.id
    
    items = await api_client.get_fridge_items(telegram_id)
    
    if not items:
        await message.answer(FRIDGE_EMPTY, reply_markup=get_main_keyboard())
        return
    
    # Group by category
    categories: dict[str, list] = {}
    expiring: list = []
    
    for item in items:
        category = item["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
        
        if item["days_until_expiry"] is not None and item["days_until_expiry"] <= 3:
            expiring.append(item)
    
    # Build message
    text = FRIDGE_TITLE
    
    for category, category_items in categories.items():
        text += f"📦 <b>{category}</b>\n"
        for item in category_items:
            expiry_text = _format_expiry(item["days_until_expiry"])
            text += f"  — {item['product_name']} ({item['quantity']}){expiry_text}\n"
        text += "\n"
    
    if expiring:
        text += EXPIRING_WARNING
        for item in expiring:
            text += f"  ⚠️ {item['product_name']} — {_format_days(item['days_until_expiry'])}\n"
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_fridge_keyboard(items)
    )

def _format_expiry(days: int | None) -> str:
    """Format expiration days for display."""
    if days is None:
        return ""
    if days <= 0:
        return " ❌"
    if days <= 3:
        return f" ⏰({days} дн.)"
    return ""

def _format_days(days: int) -> str:
    """Format days until expiry in Russian."""
    if days <= 0:
        return "истекло!"
    if days == 1:
        return "завтра"
    return f"через {days} дней"
```

### Worker

**Шаблон:**

```python
# workers/notification_worker.py

import asyncio
from datetime import date, timedelta
from typing import List

from aiogram import Bot
from sqlalchemy import select

from ..database.session import get_session
from ..models.fridge import FridgeItem
from ..models.user import User
from ..config import settings

# Messages
EXPIRING_TODAY = "🔴 <b>Сегодня истекает срок годности:</b>\n\n"
EXPIRING_SOON = "🟡 <b>Скоро истекает срок годности:</b>\n\n"
EXPIRING_ITEM = "• {product} — {days_text}\n"

async def check_expiration():
    """
    Check for expiring products and send notifications.
    
    Runs daily at configured time.
    """
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    async with get_session() as session:
        # Get all items expiring within 3 days
        today = date.today()
        target_date = today + timedelta(days=3)
        
        result = await session.execute(
            select(FridgeItem)
            .where(
                FridgeItem.expiration_date <= target_date,
                FridgeItem.expiration_date >= today
            )
        )
        items = list(result.scalars().all())
        
        # Group by user
        user_items: dict[int, List[FridgeItem]] = {}
        for item in items:
            fridge = item.fridge
            user_id = fridge.user_id
            if user_id not in user_items:
                user_items[user_id] = []
            user_items[user_id].append(item)
        
        # Send notifications
        for user_id, user_fridge_items in user_items.items():
            user = await session.get(User, user_id)
            if not user:
                continue
            
            message = _build_notification(user_fridge_items)
            
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message,
                    parse_mode="HTML"
                )
            except Exception as e:
                # Log error but continue
                print(f"Failed to send notification to {user.telegram_id}: {e}")
    
    await bot.session.close()

def _build_notification(items: List[FridgeItem]) -> str:
    """Build notification message for user."""
    today = date.today()
    
    expiring_today = []
    expiring_soon = []
    
    for item in items:
        days = (item.expiration_date - today).days
        
        if days == 0:
            expiring_today.append(item)
        else:
            expiring_soon.append(item)
    
    message = ""
    
    if expiring_today:
        message += EXPIRING_TODAY
        for item in expiring_today:
            message += EXPIRING_ITEM.format(
                product=item.product.name,
                days_text="сегодня"
            )
        message += "\n"
    
    if expiring_soon:
        message += EXPIRING_SOON
        for item in expiring_soon:
            days = (item.expiration_date - today).days
            message += EXPIRING_ITEM.format(
                product=item.product.name,
                days_text=_format_days(days)
            )
    
    return message

def _format_days(days: int) -> str:
    """Format days in Russian."""
    if days == 1:
        return "завтра"
    if days <= 4:
        return f"через {days} дня"
    return f"через {days} дней"

async def main():
    """Main entry point for worker."""
    await check_expiration()

if __name__ == "__main__":
    asyncio.run(main())
