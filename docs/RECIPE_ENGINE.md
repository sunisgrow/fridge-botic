# Recipe Recommendation Engine

Goal: suggest recipes based on products available in fridge.

---

## Example

Fridge contains:
- eggs
- milk
- cheese
- butter

Bot suggests:
- Omelette (100% match)
- Pancakes (75% match)
- Cheese sandwich (67% match)

---

## Data Model

### Recipe Schema

```python
from pydantic import BaseModel
from typing import list

class RecipeIngredient(BaseModel):
    name: str
    quantity: str | None = None
    is_optional: bool = False

class Recipe(BaseModel):
    id: int
    name: str
    description: str | None = None
    instructions: list[str]
    cooking_time_minutes: int | None = None
    servings: int = 2
    ingredients: list[RecipeIngredient]
    source_url: str | None = None
```

### Database Tables

```sql
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    instructions TEXT,
    cooking_time_minutes INTEGER,
    servings INTEGER DEFAULT 2,
    difficulty INTEGER DEFAULT 1
);

CREATE TABLE recipe_ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_name TEXT NOT NULL,
    quantity TEXT,
    is_optional BOOLEAN DEFAULT FALSE
);
```

---

## Ingredient Matching

### Normalization

```python
INGREDIENT_ALIASES = {
    'яйцо': ['яйца', 'яйцо куриное', 'яйцо куриное'],
    'молоко': ['молоко коровье', 'молоко 3.2', 'молоко 2.5'],
    'масло': ['масло сливочное', 'сливочное масло'],
    'мука': ['мука пшеничная', 'пшеничная мука'],
    'лук': ['лук репчатый', 'луковица'],
    'морковь': ['морковка', 'морковочка'],
    'картофель': ['картошка', 'картофель'],
    'помидор': ['томаты', 'томат', 'помидоры'],
}

def normalize_ingredient(name: str) -> str:
    """Normalize ingredient name."""
    name_lower = name.lower().strip()
    
    # Check aliases
    for standard, aliases in INGREDIENT_ALIASES.items():
        if name_lower in aliases or name_lower == standard:
            return standard
    
    return name_lower
```

### Matching Algorithm

```python
from rapidfuzz import fuzz

def ingredient_match_score(
    ingredient_name: str,
    fridge_items: list[str]
) -> float:
    """Calculate match score for ingredient."""
    normalized_ingredient = normalize_ingredient(ingredient_name)
    
    for item in fridge_items:
        normalized_item = normalize_ingredient(item)
        
        # Exact match
        if normalized_ingredient == normalized_item:
            return 1.0
        
        # Fuzzy match
        ratio = fuzz.ratio(normalized_ingredient, normalized_item)
        if ratio > 85:
            return ratio / 100.0
        
        # Partial match
        if normalized_ingredient in normalized_item:
            return 0.8
        if normalized_item in normalized_ingredient:
            return 0.8
    
    return 0.0
```

---

## Recipe Scoring

```python
class RecipeScorer:
    def __init__(self, fridge_items: list[str]):
        self.fridge_items = fridge_items
        self.normalized_fridge = [
            normalize_ingredient(item) for item in fridge_items
        ]
    
    def score_recipe(self, recipe: Recipe) -> dict:
        """Calculate recipe match score."""
        total_ingredients = len(recipe.ingredients)
        if total_ingredients == 0:
            return {'score': 0.0, 'missing': []}
        
        available_count = 0
        missing = []
        available = []
        
        for ingredient in recipe.ingredients:
            score = ingredient_match_score(
                ingredient.name,
                self.fridge_items
            )
            
            if ingredient.is_optional:
                # Optional ingredients don't count against score
                if score > 0.5:
                    available.append(ingredient.name)
                total_ingredients -= 1
            elif score > 0.5:
                available_count += 1
                available.append(ingredient.name)
            else:
                missing.append(ingredient.name)
        
        # Calculate score
        if total_ingredients > 0:
            match_score = available_count / total_ingredients
        else:
            match_score = 1.0
        
        return {
            'score': match_score,
            'available': available,
            'missing': missing,
            'available_count': available_count,
            'total_ingredients': total_ingredients
        }
```

---

## Recipe Ranking

```python
class RecipeRanker:
    def __init__(self, scorer: RecipeScorer):
        self.scorer = scorer
    
    def rank_recipes(
        self,
        recipes: list[Recipe],
        limit: int = 5
    ) -> list[dict]:
        """Rank recipes by match score."""
        scored = []
        
        for recipe in recipes:
            result = self.scorer.score_recipe(recipe)
            
            if result['score'] > 0.3:  # Minimum threshold
                scored.append({
                    'recipe': recipe,
                    'score': result['score'],
                    'available': result['available'],
                    'missing': result['missing']
                })
        
        # Sort by score descending
        scored.sort(key=lambda x: x['score'], reverse=True)
        
        return scored[:limit]
```

---

## Recipe Service

```python
class RecipeService:
    def __init__(
        self,
        recipe_repo: RecipeRepository,
        fridge_repo: FridgeRepository
    ):
        self.recipe_repo = recipe_repo
        self.fridge_repo = fridge_repo
    
    async def get_recommendations(
        self,
        telegram_id: int,
        limit: int = 5
    ) -> list[dict]:
        """Get recipe recommendations for user."""
        # Get fridge contents
        items = await self.fridge_repo.get_items(telegram_id)
        fridge_names = [item.product.name for item in items]
        
        # Get all recipes
        recipes = await self.recipe_repo.get_all()
        
        # Score and rank
        scorer = RecipeScorer(fridge_names)
        ranker = RecipeRanker(scorer)
        
        recommendations = ranker.rank_recipes(recipes, limit)
        
        return recommendations
```

---

## Recipe Database

### Sample Recipes

```json
[
  {
    "id": 1,
    "name": "Омлет с сыром",
    "description": "Классический омлет с сыром на завтрак",
    "instructions": [
      "Взбейте яйца с молоком",
      "Добавьте соль и перец",
      "Разогрейте сковороду с маслом",
      "Вылейте смесь на сковороду",
      "Посыпьте тёртым сыром",
      "Готовьте 3-4 минуты"
    ],
    "cooking_time_minutes": 10,
    "servings": 2,
    "ingredients": [
      {"name": "яйцо", "quantity": "3 шт", "is_optional": false},
      {"name": "молоко", "quantity": "50 мл", "is_optional": false},
      {"name": "сыр", "quantity": "50 г", "is_optional": false},
      {"name": "масло", "quantity": "10 г", "is_optional": false},
      {"name": "зелень", "quantity": "по вкусу", "is_optional": true}
    ]
  },
  {
    "id": 2,
    "name": "Блины",
    "description": "Тонкие блины на молоке",
    "instructions": [
      "Смешайте яйца с молоком",
      "Добавьте муку и сахар",
      "Перемешайте до однородности",
      "Добавьте масло",
      "Жарьте на разогретой сковороде"
    ],
    "cooking_time_minutes": 30,
    "servings": 4,
    "ingredients": [
      {"name": "яйцо", "quantity": "2 шт", "is_optional": false},
      {"name": "молоко", "quantity": "500 мл", "is_optional": false},
      {"name": "мука", "quantity": "200 г", "is_optional": false},
      {"name": "масло", "quantity": "30 г", "is_optional": false},
      {"name": "сахар", "quantity": "2 ст.л.", "is_optional": false}
    ]
  }
]
```

---

## API Endpoint

```python
@router.get("/recipes")
async def get_recipes(
    telegram_id: int,
    limit: int = 5,
    service: RecipeService = Depends()
):
    """Get recipe recommendations."""
    recommendations = await service.get_recommendations(
        telegram_id,
        limit
    )
    
    return {
        "recipes": [
            {
                "id": r['recipe'].id,
                "name": r['recipe'].name,
                "cooking_time_minutes": r['recipe'].cooking_time_minutes,
                "match_score": r['score'],
                "available_ingredients": [
                    {"name": i, "available": True}
                    for i in r['available']
                ],
                "missing_ingredients": [
                    {"name": i, "available": False}
                    for i in r['missing']
                ]
            }
            for r in recommendations
        ]
    }
```

---

## Bot Integration

```python
@router.message(F.text == "🍳 Рецепты")
async def show_recipes(message: Message, api_client: APIClient):
    """Show recipe recommendations."""
    telegram_id = message.from_user.id
    
    recipes = await api_client.get_recipes(telegram_id)
    
    if not recipes:
        await message.answer(
            "К сожалению, не нашлось подходящих рецептов. "
            "Попробуйте добавить больше продуктов."
        )
        return
    
    text = "🍳 Рецепты из ваших продуктов:\n\n"
    
    for recipe in recipes:
        score_percent = int(recipe['match_score'] * 100)
        text += f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"🍽️ {recipe['name']}\n\n"
        text += f"Совпадение: {score_percent}%\n"
        text += f"⏱️ Время: {recipe['cooking_time_minutes']} мин.\n\n"
        
        text += "✅ Есть:\n"
        for ing in recipe['available_ingredients']:
            text += f"   • {ing['name']}\n"
        
        if recipe['missing_ingredients']:
            text += "\n❌ Не хватает:\n"
            for ing in recipe['missing_ingredients']:
                text += f"   • {ing['name']}\n"
        
        text += "\n"
    
    await message.answer(text)
```

---

## Future Improvements

1. **Diet Filters**
   - Vegetarian, vegan, gluten-free
   - Allergy restrictions

2. **Calorie Calculation**
   - Estimate calories per serving
   - Nutritional information

3. **AI Recipe Generation**
   - Generate recipes from available ingredients
   - Use LLM for creative suggestions

4. **Recipe Sources**
   - Import from popular cooking sites
   - User-submitted recipes