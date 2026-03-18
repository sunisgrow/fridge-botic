# Service Dependencies

Полная карта зависимостей между модулями проекта Fridge Bot.

---

## Общая диаграмма зависимостей

```
┌─────────────────────────────────────────────────────────────────────┐
│                           TELEGRAM USER                             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          BOT LAYER (aiogram)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ handlers│ │keyboards│ │ states  │ │ services│ │  utils  │       │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │
└───────┼──────────┼──────────┼──────────┼──────────┼─────────────────┘
        │          │          │          │          │
        └──────────┴──────────┴──────────┼──────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API CLIENT (httpx)                          │
└─────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API LAYER (FastAPI)                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │ routers │ │services │ │  repos  │ │ schemas │ │  utils  │       │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │
└───────┼──────────┼──────────┼──────────┼──────────┼─────────────────┘
        │          │          │          │          │
        └──────────┴──────────┴──────────┼──────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DATABASE LAYER (SQLAlchemy)                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│  │ session │ │  base   │ │ models  │ │migrations│                  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        PostgreSQL Database                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Детальные зависимости по слоям

### 1. Bot Layer

```
bot/
├── main.py
│   └── depends on: config.py, handlers/*, aiogram
│
├── config.py
│   └── depends on: os, pydantic-settings
│
├── handlers/
│   ├── start.py
│   │   └── depends on: aiogram, keyboards/main_menu.py, services/api_client.py
│   │
│   ├── add_product.py
│   │   └── depends on: aiogram, states/add_product_state.py,
│   │                    keyboards/categories.py, services/api_client.py
│   │
│   ├── scan_product.py
│   │   └── depends on: aiogram, states/scan_state.py,
│   │                    services/api_client.py
│   │
│   ├── fridge_view.py
│   │   └── depends on: aiogram, keyboards/fridge.py, services/api_client.py
│   │
│   ├── expiring_products.py
│   │   └── depends on: aiogram, services/api_client.py
│   │
│   ├── recipes.py
│   │   └── depends on: aiogram, services/api_client.py
│   │
│   ├── shopping_list.py
│   │   └── depends on: aiogram, services/api_client.py
│   │
│   └── settings.py
│       └── depends on: aiogram, services/api_client.py
│
├── keyboards/
│   ├── main_menu.py
│   │   └── depends on: aiogram.types
│   │
│   ├── categories.py
│   │   └── depends on: aiogram.types
│   │
│   ├── confirmation.py
│   │   └── depends on: aiogram.types
│   │
│   └── fridge.py
│       └── depends on: aiogram.types
│
├── states/
│   ├── add_product_state.py
│   │   └── depends on: aiogram.fsm
│   │
│   └── scan_state.py
│       └── depends on: aiogram.fsm
│
└── services/
    └── api_client.py
        └── depends on: httpx, config.py
```

---

### 2. API Layer

```
api/
├── main.py
│   └── depends on: fastapi, routers/*, database/session.py
│
├── config.py
│   └── depends on: os, pydantic-settings
│
├── routers/
│   ├── users.py
│   │   └── depends on: fastapi, services/user_service.py,
│   │                    schemas/user_schema.py
│   │
│   ├── products.py
│   │   └── depends on: fastapi, services/product_service.py,
│   │                    schemas/product_schema.py
│   │
│   ├── fridge.py
│   │   └── depends on: fastapi, services/fridge_service.py,
│   │                    schemas/fridge_schema.py
│   │
│   ├── scan.py
│   │   └── depends on: fastapi, services/scan_service.py,
│   │                    schemas/scan_schema.py
│   │
│   ├── notifications.py
│   │   └── depends on: fastapi, services/notification_service.py,
│   │                    schemas/notification_schema.py
│   │
│   ├── recipes.py
│   │   └── depends on: fastapi, services/recipe_service.py,
│   │                    schemas/recipe_schema.py
│   │
│   └── shopping.py
│       └── depends on: fastapi, services/shopping_service.py,
│                        schemas/shopping_schema.py
│
├── services/
│   ├── user_service.py
│   │   └── depends on: repositories/user_repo.py, schemas/user_schema.py
│   │
│   ├── product_service.py
│   │   └── depends on: repositories/product_repo.py,
│   │                    repositories/category_repo.py,
│   │                    ml/product_classifier/inference.py (optional),
│   │                    schemas/product_schema.py
│   │
│   ├── fridge_service.py
│   │   └── depends on: repositories/fridge_repo.py,
│   │                    repositories/product_repo.py,
│   │                    repositories/user_repo.py,
│   │                    schemas/fridge_schema.py
│   │
│   ├── scan_service.py
│   │   └── depends on: repositories/scan_repo.py,
│   │                    repositories/product_repo.py,
│   │                    scanner/datamatrix_decoder.py,
│   │                    scanner/gs1_parser.py,
│   │                    schemas/scan_schema.py
│   │
│   ├── notification_service.py
│   │   └── depends on: repositories/notification_repo.py,
│   │                    repositories/fridge_repo.py,
│   │                    schemas/notification_schema.py
│   │
│   ├── recipe_service.py
│   │   └── depends on: repositories/fridge_repo.py,
│   │                    recipe_engine/recipe_matcher.py,
│   │                    recipe_engine/recipe_ranker.py,
│   │                    schemas/recipe_schema.py
│   │
│   └── shopping_service.py
│       └── depends on: repositories/fridge_repo.py,
│                       shopping_engine/list_generator.py,
│                       schemas/shopping_schema.py
│
├── repositories/
│   ├── user_repo.py
│   │   └── depends on: database/session.py, models/user.py
│   │
│   ├── product_repo.py
│   │   └── depends on: database/session.py, models/product.py,
│   │                    models/category.py, models/brand.py
│   │
│   ├── fridge_repo.py
│   │   └── depends on: database/session.py, models/fridge.py,
│   │                    models/fridge_item.py
│   │
│   ├── scan_repo.py
│   │   └── depends on: database/session.py, models/datamatrix.py,
│   │                    models/scan_log.py
│   │
│   └── notification_repo.py
│       └── depends on: database/session.py, models/notification.py
│
├── schemas/
│   ├── user_schema.py ─────── depends on: pydantic
│   ├── product_schema.py ──── depends on: pydantic
│   ├── fridge_schema.py ───── depends on: pydantic
│   ├── scan_schema.py ─────── depends on: pydantic
│   ├── notification_schema.py depends on: pydantic
│   ├── recipe_schema.py ───── depends on: pydantic
│   └── shopping_schema.py ─── depends on: pydantic
│
├── models/
│   ├── user.py ────────────── depends on: sqlalchemy, database/base.py
│   ├── product.py ─────────── depends on: sqlalchemy, database/base.py
│   ├── fridge.py ──────────── depends on: sqlalchemy, database/base.py
│   ├── datamatrix.py ──────── depends on: sqlalchemy, database/base.py
│   ├── recipe.py ──────────── depends on: sqlalchemy, database/base.py
│   └── notification.py ────── depends on: sqlalchemy, database/base.py
│
└── database/
    ├── session.py ─────────── depends on: sqlalchemy.ext.asyncio, config.py
    └── base.py ────────────── depends on: sqlalchemy.orm
```

---

### 3. Workers Layer

```
workers/
├── scan_worker.py
│   └── depends on: celery/redis, scanner/datamatrix_decoder.py,
│                   scanner/image_preprocessing.py, scanner/gs1_parser.py,
│                   api/repositories/scan_repo.py,
│                   api/repositories/product_repo.py
│
├── notification_worker.py
│   └── depends on: celery/redis, aiogram,
│                   api/repositories/fridge_repo.py,
│                   api/repositories/notification_repo.py,
│                   api/config.py
│
├── import_worker.py
│   └── depends on: celery/redis, importers/gtin_importer.py,
│                   api/repositories/product_repo.py
│
└── analytics_worker.py
    └── depends on: celery/redis,
                    api/repositories/fridge_repo.py,
                    api/repositories/notification_repo.py
```

---

### 4. Scanner Layer

```
scanner/
├── datamatrix_decoder.py
│   └── depends on: cv2, pyzbar/zxing-cpp, numpy
│
├── image_preprocessing.py
│   └── depends on: cv2, numpy
│
└── gs1_parser.py
    └── depends on: re, datetime
```

---

### 5. ML Layer

```
ml/
├── product_classifier/
│   ├── train_model.py
│   │   └── depends on: sklearn/fasttext, pandas, data/training_data.csv
│   │
│   ├── model.py
│   │   └── depends on: sklearn/fasttext, pickle/joblib
│   │
│   └── inference.py
│       └── depends on: model.py, numpy
│
└── models/
    └── product_classifier.bin
```

---

### 6. Recipe Engine Layer

```
recipe_engine/
├── recipe_matcher.py
│   └── depends on: data/recipes_dataset.json, rapidfuzz
│
├── recipe_ranker.py
│   └── depends on: recipe_matcher.py
│
└── data/
    └── recipes_dataset.json
```

---

### 7. Shopping Engine Layer

```
shopping_engine/
├── list_generator.py
│   └── depends on: api/repositories/fridge_repo.py,
│                   recipe_engine/recipe_matcher.py
│
└── purchase_predictor.py
    └── depends on: api/repositories/fridge_repo.py,
                    collections/Counter
```

---

### 8. Importers Layer

```
importers/
├── gtin_importer.py
│   └── depends on: pandas, api/database/session.py,
│                   api/models/product.py
│
├── openfoodfacts_importer.py
│   └── depends on: requests, gtin_importer.py
│
└── retail_catalog_importer.py
    └── depends on: requests, gtin_importer.py
```

---

## Внешние зависимости

### Python Packages

```toml
# pyproject.toml

[project]
dependencies = [
    # Bot
    "aiogram>=3.0.0",
    
    # API
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    
    # Database
    "sqlalchemy>=2.0.0",
    "asyncpg>=0.28.0",
    "alembic>=1.12.0",
    
    # HTTP Client
    "httpx>=0.24.0",
    
    # Scanner
    "opencv-python>=4.8.0",
    "pyzbar>=0.1.9",
    "numpy>=1.24.0",
    
    # Queue/Workers
    "celery>=5.3.0",
    "redis>=4.5.0",
    
    # ML (optional)
    "scikit-learn>=1.3.0",
    "rapidfuzz>=3.0.0",
    
    # Utils
    "python-dateutil>=2.8.0",
    "python-dotenv>=1.0.0",
]
```

---

## Порядок инициализации сервисов

### Startup Sequence

```
1. PostgreSQL
   └── Required by: API, Workers

2. Redis
   └── Required by: Workers, Bot (FSM storage)

3. API Server
   └── Required by: Bot

4. Workers
   └── Required by: API (async tasks)

5. Bot
   └── Required by: User
```

### Docker Compose Order

```yaml
services:
  postgres:
    # No dependencies

  redis:
    # No dependencies

  api:
    depends_on:
      - postgres
      - redis

  worker-scan:
    depends_on:
      - postgres
      - redis

  worker-notification:
    depends_on:
      - postgres
      - redis

  bot:
    depends_on:
      - api
```

---

## Зависимости данных

### Data Flow Dependencies

```
User Data:
  users → fridges → fridge_items
                    ↓
               products → categories
                    ↓
                   brands

Scan Data:
  scan_logs → datamatrix_codes
       ↓           ↓
    users       gtin → products

Notification Data:
  notification_settings → users
  notification_queue → fridge_items → users

Recipe Data:
  recipes → recipe_ingredients
       ↓
  matched with fridge_items
```

---

## Критические пути

### Path 1: Add Product

```
Bot Handler
    → API Client
        → API Router (fridge.py)
            → FridgeService
                → FridgeRepository
                    → Database
                → ProductRepository
                    → Database
```

### Path 2: Scan DataMatrix

```
Bot Handler
    → API Client
        → API Router (scan.py)
            → ScanService
                → ScanRepository
                → Scanner (datamatrix_decoder.py)
                    → Image Preprocessing
                    → GS1 Parser
                → ProductRepository
                    → GTIN Lookup
            → Queue (Redis)
                → Scan Worker
                    → Database
```

### Path 3: Notification

```
Scheduler (APScheduler)
    → Notification Worker
        → FridgeRepository
            → Database (expiring items)
        → Telegram API
            → User
```

---

## Изоляция слоёв

### Правила изоляции

1. **Bot Layer** НЕ должен:
   - Импортировать models напрямую
   - Импортировать repositories
   - Обращаться к Database

2. **API Layer** НЕ должен:
   - Импортировать bot handlers
   - Знать о Telegram API

3. **Workers** НЕ должны:
   - Знать о HTTP клиентах
   - Импортировать bot handlers

4. **Scanner** НЕ должен:
   - Знать о Database
   - Знать о API структуре

### Разрешённые зависимости

```
Bot → API Client → API
API → Services → Repositories → Models → Database
Workers → Repositories → Models → Database
Scanner → (standalone, no DB/API dependencies)
ML → (standalone, no DB/API dependencies)
```

---

## Кэширование

### Redis Cache Layers

```
1. FSM State Cache
   Used by: Bot (aiogram)
   Key pattern: fsm:{user_id}:{key}

2. GTIN Cache
   Used by: ProductService
   Key pattern: gtin:{gtin_code}
   TTL: 24 hours

3. Session Cache
   Used by: API (rate limiting)
   Key pattern: session:{telegram_id}
   TTL: 1 hour

4. Task Queue
   Used by: Workers (Celery)
   Key pattern: celery:*
```

---

## Конфигурация окружения

### Environment Variables

```bash
# .env

# Telegram
TELEGRAM_BOT_TOKEN=xxx

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/fridge_bot

# Redis
REDIS_URL=redis://redis:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000

# Workers
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

---

## Мониторинг зависимостей

### Health Check Endpoints

```
/api/health
    → Check PostgreSQL connection
    → Check Redis connection
    → Return status

/api/health/ready
    → All dependencies ready
    → Service can accept requests

/api/health/live
    → Service is running
    → Basic liveness probe
```
