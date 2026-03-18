# Shopping List Engine

Goal: automatically generate shopping list based on fridge state.

---

## Sources for Shopping List

1. **Expiring Products** - Items that need replacement
2. **Frequently Used Products** - Items often consumed
3. **Recipe Requirements** - Missing ingredients for recipes
4. **User Preferences** - Manually added items

---

## Data Model

```python
from pydantic import BaseModel
from datetime import date
from typing import Literal

class ShoppingItem(BaseModel):
    id: int
    product_name: str
    quantity: int = 1
    reason: Literal['expiring', 'frequent', 'recipe', 'manual']
    is_purchased: bool = False
    recipe_id: int | None = None

class ShoppingList(BaseModel):
    id: int
    items: list[ShoppingItem]
    created_at: date
    is_completed: bool = False
```

---

## List Generator

```python
class ShoppingListGenerator:
    def __init__(
        self,
        fridge_repo: FridgeRepository,
        stats_repo: ProductStatsRepository
    ):
        self.fridge_repo = fridge_repo
        self.stats_repo = stats_repo
    
    async def generate(
        self,
        telegram_id: int,
        recipe_service: RecipeService | None = None
    ) -> list[ShoppingItem]:
        """Generate shopping list."""
        items = []
        
        # 1. Expiring products
        expiring = await self._get_expiring_items(telegram_id)
        items.extend(expiring)
        
        # 2. Frequently used products
        frequent = await self._get_frequent_items(telegram_id)
        items.extend(frequent)
        
        # 3. Recipe requirements (optional)
        if recipe_service:
            recipe_items = await self._get_recipe_items(
                telegram_id,
                recipe_service
            )
            items.extend(recipe_items)
        
        # Deduplicate
        items = self._deduplicate(items)
        
        return items
    
    async def _get_expiring_items(
        self,
        telegram_id: int
    ) -> list[ShoppingItem]:
        """Get items that are expiring soon."""
        items = []
        
        expiring = await self.fridge_repo.get_expiring_items(
            telegram_id,
            days=3
        )
        
        for item in expiring:
            items.append(ShoppingItem(
                product_name=item.product.name,
                quantity=item.quantity,
                reason='expiring'
            ))
        
        return items
    
    async def _get_frequent_items(
        self,
        telegram_id: int
    ) -> list[ShoppingItem]:
        """Get frequently consumed items that are low."""
        items = []
        
        # Get products used frequently
        stats = await self.stats_repo.get_top_products(
            telegram_id,
            limit=10
        )
        
        # Check if they're in fridge
        fridge_items = await self.fridge_repo.get_items(telegram_id)
        fridge_names = {i.product.name for i in fridge_items}
        
        for stat in stats:
            if stat.product.name not in fridge_names:
                items.append(ShoppingItem(
                    product_name=stat.product.name,
                    quantity=1,
                    reason='frequent'
                ))
        
        return items
    
    async def _get_recipe_items(
        self,
        telegram_id: int,
        recipe_service: RecipeService
    ) -> list[ShoppingItem]:
        """Get missing ingredients for top recipes."""
        items = []
        
        recommendations = await recipe_service.get_recommendations(
            telegram_id,
            limit=3
        )
        
        for rec in recommendations:
            if rec['score'] > 0.5:  # Good match
                for missing in rec['missing']:
                    items.append(ShoppingItem(
                        product_name=missing,
                        quantity=1,
                        reason='recipe',
                        recipe_id=rec['recipe'].id
                    ))
        
        return items
    
    def _deduplicate(
        self,
        items: list[ShoppingItem]
    ) -> list[ShoppingItem]:
        """Remove duplicate items, keep best reason."""
        seen = {}
        
        for item in items:
            name = item.product_name.lower()
            
            if name not in seen:
                seen[name] = item
            else:
                # Prefer expiring > recipe > frequent > manual
                priority = {'expiring': 4, 'recipe': 3, 'frequent': 2, 'manual': 1}
                if priority[item.reason] > priority[seen[name].reason]:
                    seen[name] = item
        
        return list(seen.values())
```

---

## Purchase Predictor

```python
class PurchasePredictor:
    """Predict products user might need."""
    
    def __init__(self, stats_repo: ProductStatsRepository):
        self.stats_repo = stats_repo
    
    async def predict(
        self,
        telegram_id: int
    ) -> list[dict]:
        """Predict purchases based on history."""
        predictions = []
        
        # Get purchase patterns
        stats = await self.stats_repo.get_user_stats(telegram_id)
        
        for stat in stats:
            # Calculate average time between purchases
            avg_days = stat.total_days / stat.times_added
            
            # Days since last purchase
            days_since = (date.today() - stat.last_added).days
            
            # Predict if likely to need soon
            if days_since >= avg_days * 0.8:
                predictions.append({
                    'product': stat.product.name,
                    'probability': days_since / avg_days,
                    'reason': 'regular_purchase'
                })
        
        # Sort by probability
        predictions.sort(key=lambda x: x['probability'], reverse=True)
        
        return predictions[:5]
```

---

## Shopping Service

```python
class ShoppingService:
    def __init__(
        self,
        generator: ShoppingListGenerator,
        predictor: PurchasePredictor,
        shopping_repo: ShoppingRepository
    ):
        self.generator = generator
        self.predictor = predictor
        self.shopping_repo = shopping_repo
    
    async def get_or_create_list(
        self,
        telegram_id: int
    ) -> ShoppingList:
        """Get active shopping list or create new."""
        # Check for existing active list
        existing = await self.shopping_repo.get_active_list(telegram_id)
        
        if existing:
            return existing
        
        # Generate new list
        items = await self.generator.generate(telegram_id)
        
        # Create list in database
        shopping_list = await self.shopping_repo.create_list(
            telegram_id,
            items
        )
        
        return shopping_list
    
    async def add_item(
        self,
        telegram_id: int,
        product_name: str,
        quantity: int = 1
    ) -> ShoppingItem:
        """Add item manually."""
        item = ShoppingItem(
            product_name=product_name,
            quantity=quantity,
            reason='manual'
        )
        
        return await self.shopping_repo.add_item(telegram_id, item)
    
    async def mark_purchased(
        self,
        item_id: int
    ) -> bool:
        """Mark item as purchased."""
        return await self.shopping_repo.update_item(
            item_id,
            {'is_purchased': True}
        )
    
    async def complete_list(
        self,
        telegram_id: int
    ) -> None:
        """Mark list as completed."""
        await self.shopping_repo.complete_list(telegram_id)
```

---

## API Endpoints

```python
@router.get("/shopping")
async def get_shopping_list(
    telegram_id: int,
    service: ShoppingService = Depends()
):
    """Get active shopping list."""
    shopping_list = await service.get_or_create_list(telegram_id)
    
    return {
        "list": {
            "id": shopping_list.id,
            "items": [
                {
                    "id": item.id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "reason": item.reason,
                    "is_purchased": item.is_purchased
                }
                for item in shopping_list.items
            ],
            "total_items": len(shopping_list.items),
            "purchased_count": sum(1 for i in shopping_list.items if i.is_purchased)
        }
    }

@router.post("/shopping/items")
async def add_shopping_item(
    data: ShoppingItemCreate,
    service: ShoppingService = Depends()
):
    """Add item to shopping list."""
    item = await service.add_item(
        data.telegram_id,
        data.product_name,
        data.quantity
    )
    
    return {"id": item.id, "created": True}

@router.patch("/shopping/items/{item_id}")
async def update_shopping_item(
    item_id: int,
    data: ShoppingItemUpdate,
    service: ShoppingService = Depends()
):
    """Update shopping item."""
    if data.is_purchased:
        await service.mark_purchased(item_id)
    
    return {"updated": True}

@router.post("/shopping/complete")
async def complete_shopping(
    telegram_id: int,
    service: ShoppingService = Depends()
):
    """Complete shopping list."""
    await service.complete_list(telegram_id)
    
    # Optionally add purchased items to fridge
    # ...
    
    return {"completed": True}
```

---

## Bot Integration

```python
@router.message(F.text == "🛒 Покупки")
async def show_shopping_list(message: Message, api_client: APIClient):
    """Show shopping list."""
    telegram_id = message.from_user.id
    
    result = await api_client.get_shopping_list(telegram_id)
    shopping_list = result['list']
    
    if not shopping_list['items']:
        await message.answer(
            "🛒 Список покупок пуст!\n\n"
            "Добавьте продукты вручную или система "
            "автоматически предложит нужное.",
            reply_markup=get_add_item_keyboard()
        )
        return
    
    text = "🛒 Список покупок:\n\n"
    
    # Group by reason
    by_reason = {
        'expiring': [],
        'frequent': [],
        'recipe': [],
        'manual': []
    }
    
    for item in shopping_list['items']:
        by_reason[item['reason']].append(item)
    
    if by_reason['expiring']:
        text += "⚠️ Заканчивается:\n"
        for item in by_reason['expiring']:
            status = "✅" if item['is_purchased'] else "☐"
            text += f"  {status} {item['product_name']} × {item['quantity']}\n"
        text += "\n"
    
    if by_reason['recipe']:
        text += "🍳 Для рецептов:\n"
        for item in by_reason['recipe']:
            status = "✅" if item['is_purchased'] else "☐"
            text += f"  {status} {item['product_name']}\n"
        text += "\n"
    
    if by_reason['frequent']:
        text += "🔄 Часто покупаете:\n"
        for item in by_reason['frequent']:
            status = "✅" if item['is_purchased'] else "☐"
            text += f"  {status} {item['product_name']}\n"
        text += "\n"
    
    if by_reason['manual']:
        text += "📝 Добавлено вручную:\n"
        for item in by_reason['manual']:
            status = "✅" if item['is_purchased'] else "☐"
            text += f"  {status} {item['product_name']}\n"
    
    text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"Всего: {shopping_list['total_items']} позиций\n"
    text += f"Куплено: {shopping_list['purchased_count']}"
    
    await message.answer(
        text,
        reply_markup=get_shopping_keyboard(shopping_list['items'])
    )
```

---

## Keyboard Actions

```python
def get_shopping_keyboard(items: list) -> InlineKeyboardMarkup:
    """Generate keyboard for shopping list."""
    builder = InlineKeyboardBuilder()
    
    for item in items:
        if not item['is_purchased']:
            builder.button(
                text=f"✓ {item['product_name']}",
                callback_data=f"buy:{item['id']}"
            )
    
    builder.button(text="➕ Добавить", callback_data="shop:add")
    builder.button(text="🗑️ Очистить", callback_data="shop:clear")
    builder.button(text="✅ Завершить", callback_data="shop:complete")
    
    builder.adjust(1)
    return builder.as_markup()
```

---

## Future Features

1. **Price Tracking**
   - Track product prices
   - Show estimated total

2. **Store Integration**
   - Sync with online stores
   - One-click ordering

3. **Shared Lists**
   - Family shopping lists
   - Real-time updates

4. **Smart Suggestions**
   - ML-based predictions
   - Seasonal recommendations