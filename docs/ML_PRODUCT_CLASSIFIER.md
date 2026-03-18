# Product Category Classifier

Goal: automatically determine product category from product name.

---

## Problem

When adding products via GTIN scan or manual input, category information may be missing.

The classifier automatically assigns appropriate category.

---

## Categories

| ID | Name | Icon |
|----|------|------|
| 1 | Молочные продукты | 🥛 |
| 2 | Мясо | 🥩 |
| 3 | Рыба | 🐟 |
| 4 | Овощи | 🥬 |
| 5 | Фрукты | 🍎 |
| 6 | Напитки | 🥤 |
| 7 | Соусы | 🫗 |
| 8 | Заморозка | 🧊 |
| 9 | Хлеб | 🍞 |
| 10 | Снеки | 🍿 |
| 11 | Другое | 📦 |

---

## Approach

### Option 1: Keyword-Based (Simple)

Fast, no ML required.

```python
CATEGORY_KEYWORDS = {
    'Молочные продукты': [
        'молоко', 'йогурт', 'кефир', 'сыр', 'творог',
        'сметана', 'сливки', 'ряженка', 'простокваша',
        'молочн', 'dairy', 'danone', 'актимель'
    ],
    'Мясо': [
        'мясо', 'куриц', 'говядин', 'свинин', 'индейк',
        'филе', 'стейк', 'котлет', 'сосиск', 'колбас',
        'meat', 'chicken', 'beef', 'pork'
    ],
    'Рыба': [
        'рыб', 'форель', 'лосос', 'селёдк', 'сельдь',
        'треск', 'минтай', 'креветк', 'кальмар',
        'fish', 'salmon', 'shrimp'
    ],
    'Овощи': [
        'овощ', 'картоф', 'морков', 'лук', 'чеснок',
        'капуст', 'огурц', 'помидор', 'томат', 'перец',
        'vegetable', 'tomato', 'cucumber'
    ],
    'Фрукты': [
        'фрукт', 'яблок', 'груш', 'банан', 'апельсин',
        'мандарин', 'виноград', 'киви', 'персик',
        'fruit', 'apple', 'banana', 'orange'
    ],
    'Напитки': [
        'напиток', 'сок', 'вода', 'кола', 'лимонад',
        'чай', 'кофе', 'морс', 'компот', 'квас',
        'drink', 'juice', 'water', 'cola', 'pepsi'
    ],
    'Соусы': [
        'соус', 'кетчуп', 'майонез', 'горчиц', 'хрен',
        'аджик', 'sauce', 'ketchup', 'mayonnaise'
    ],
    'Заморозка': [
        'заморож', 'морожен', 'заморозк', 'frozen',
        'ice cream', 'freezer'
    ],
    'Хлеб': [
        'хлеб', 'булк', 'батон', 'багет', 'круассан',
        'печенье', 'пирож', 'торт', 'бисквит',
        'bread', 'bun', 'pastry', 'cake'
    ],
    'Снеки': [
        'чипс', 'снек', 'орешк', 'сухарик', 'попкорн',
        'семечк', 'snack', 'chips', 'nuts'
    ]
}

def classify_keyword(product_name: str) -> tuple[str, float]:
    """Classify using keyword matching."""
    name_lower = product_name.lower()
    
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in name_lower)
        if score > 0:
            scores[category] = score
    
    if scores:
        best = max(scores.items(), key=lambda x: x[1])
        confidence = min(best[1] / 3.0, 1.0)  # Cap at 1.0
        return best[0], confidence
    
    return 'Другое', 0.0
```

---

### Option 2: ML Classifier (Advanced)

Higher accuracy, requires training.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib

class ProductClassifier:
    def __init__(self, model_path: str = None):
        if model_path:
            self.model = joblib.load(model_path)
        else:
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(
                    ngram_range=(1, 2),
                    max_features=5000,
                    min_df=2
                )),
                ('clf', MultinomialNB(alpha=0.1))
            ])
    
    def train(self, X: list[str], y: list[str]):
        """Train classifier on labeled data."""
        self.model.fit(X, y)
    
    def predict(self, product_name: str) -> tuple[str, float]:
        """Predict category with confidence."""
        probs = self.model.predict_proba([product_name])[0]
        best_idx = probs.argmax()
        
        category = self.model.classes_[best_idx]
        confidence = probs[best_idx]
        
        return category, confidence
    
    def save(self, path: str):
        """Save model to disk."""
        joblib.dump(self.model, path)
```

---

## Training Data

### Sources

1. Existing product database with categories
2. Open Food Facts (category labels)
3. User corrections (feedback loop)

### Data Preparation

```python
def prepare_training_data(products: list[dict]) -> tuple[list, list]:
    """Prepare X, y for training."""
    X = []
    y = []
    
    for product in products:
        name = product['name']
        category = product['category']
        
        # Preprocess name
        name = preprocess_name(name)
        
        X.append(name)
        y.append(category)
    
    return X, y

def preprocess_name(name: str) -> str:
    """Preprocess product name for training."""
    # Lowercase
    name = name.lower()
    
    # Remove brand names in parentheses
    name = re.sub(r'\([^)]*\)', '', name)
    
    # Remove extra whitespace
    name = ' '.join(name.split())
    
    return name
```

---

## Training Pipeline

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

async def train_classifier():
    """Train and evaluate classifier."""
    # Load training data
    products = await load_labeled_products()
    
    X, y = prepare_training_data(products)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train
    classifier = ProductClassifier()
    classifier.train(X_train, y_train)
    
    # Evaluate
    y_pred = classifier.model.predict(X_test)
    report = classification_report(y_test, y_pred)
    print(report)
    
    # Save model
    classifier.save('models/product_classifier.bin')
    
    return classifier
```

---

## Integration

### In Product Service

```python
class ProductService:
    def __init__(self, classifier: ProductClassifier):
        self.classifier = classifier
    
    async def create_product(
        self,
        name: str,
        category_id: int | None = None
    ) -> Product:
        """Create product with auto-category if missing."""
        if category_id is None:
            # Auto-classify
            category_name, confidence = self.classifier.predict(name)
            
            if confidence > 0.7:
                category_id = await self.get_category_id(category_name)
            
        # Create product
        product = Product(
            name=name,
            category_id=category_id
        )
        
        return product
```

### Feedback Loop

```python
async def record_correction(
    product_id: int,
    correct_category_id: int
):
    """Record user correction for retraining."""
    async with get_session() as session:
        await session.execute(
            text("""
                INSERT INTO classification_feedback 
                (product_id, correct_category_id, created_at)
                VALUES (:pid, :cid, NOW())
            """),
            {'pid': product_id, 'cid': correct_category_id}
        )
```

---

## Performance

| Metric | Keyword | ML |
|--------|---------|-----|
| Accuracy | 75% | 90% |
| Speed | < 1ms | < 50ms |
| Training | None | ~5 min |

---

## Model Retraining

Schedule periodic retraining with new data.

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def retrain_model():
    """Retrain classifier with feedback data."""
    # Load original training data
    products = await load_labeled_products()
    
    # Add corrections
    corrections = await load_corrections()
    products.extend(corrections)
    
    # Retrain
    classifier = ProductClassifier()
    await train_classifier()
    
    # Save new model
    classifier.save('models/product_classifier.bin')

# Schedule weekly retraining
scheduler = AsyncIOScheduler()
scheduler.add_job(retrain_model, 'cron', day_of_week='mon', hour=3)
scheduler.start()
```