# [DISABLED] # KODA.md — Инструкции для AI-агента

## Описание проекта

**Fridge Bot** — Telegram-платформа для управления продуктами в холодильнике с поддержкой сканирования DataMatrix кодов из системы «Честный знак». Платформа позволяет пользователям отслеживать сроки годности, получать рекомендации по рецептам и формировать списки покупок.

---

## Архитектура системы

### Общая схема

```
Telegram
    ↓
Bot Service (aiogram)
    ↓
API Backend (FastAPI)
    ↓
Database (PostgreSQL) + Queue/Cache (Redis)
    ↓
Background Workers
```

### Основные сервисы

| Сервис | Технология | Назначение |
|--------|------------|------------|
| Bot Service | aiogram 3.x | Обработка команд Telegram, FSM диалоги |
| API Backend | FastAPI | Бизнес-логика, REST API |
| Database | PostgreSQL | Хранение данных пользователей, продуктов, холодильника |
| Queue/Cache | Redis | Очередь задач, кэш GTIN, FSM состояния |
| Workers | Python/Celery | Фоновая обработка задач |

---

## Технологический стек

| Категория | Технологии |
|-----------|------------|
| Bot Framework | aiogram 3.4.1 |
| API Framework | FastAPI 0.109.0 |
| Database | PostgreSQL 15 |
| Cache/Queue | Redis 7 |
| ORM | SQLAlchemy 2.0.25 (async) |
| Validation | Pydantic 2.5.3 |
| Image Processing | OpenCV 4.9.0, zxing-cpp 2.1.0 |
| ML | scikit-learn, FastText |
| Containerization | Docker, Docker Compose |
| Testing | pytest, pytest-asyncio, pytest-cov |

---

## Структура проекта

```
/
├── bot/                    # Telegram бот
│   ├── config.py          # Конфигурация
│   ├── handlers/          # Обработчики команд
│   ├── keyboards/         # Клавиатуры
│   ├── states/            # FSM состояния
│   ├── services/          # API клиент
│   └── main.py            # Точка входа
│
├── api/                    # REST API
│   ├── config.py          # Конфигурация
│   ├── database/          # Подключение к БД
│   ├── models/            # SQLAlchemy модели
│   ├── repositories/      # Репозитории данных
│   ├── routers/           # API роуты
│   ├── schemas/           # Pydantic схемы
│   ├── services/          # Бизнес-логика
│   └── main.py            # Точка входа
│
├── scanner/               # Модуль сканирования DataMatrix
│   ├── datamatrix_decoder.py   # Декодирование кодов
│   ├── gs1_parser.py           # Парсинг GS1 формата
│   ├── image_preprocessing.py  # Предобработка изображений
│   └── __init__.py
│
├── workers/               # Фоновые обработчики
│   ├── scan_worker.py          # Обработка сканов
│   ├── notification_worker.py  # Уведомления
│   ├── import_worker.py        # Импорт GTIN
│   └── analytics_worker.py     # Аналитика
│
├── ml/                    # Machine Learning модули
│   ├── product_classifier/     # Классификация продуктов
│   │   ├── train_model.py
│   │   ├── model.py
│   │   ├── inference.py
│   │   └── models/
│   ├── recipe_engine/          # Рекомендации рецептов
│   │   ├── recipe_matcher.py
│   │   ├── recipe_ranker.py
│   │   └── data/
│   │       └── recipes_dataset.json
│   └── shopping_engine/        # Генерация списка покупок
│       ├── list_generator.py
│       └── purchase_predictor.py
│
├── importers/             # Импорт данных
│   ├── gtin_importer.py
│   ├── openfoodfacts_importer.py
│   └── retail_catalog_importer.py
│
├── data/                  # Статические данные
│   ├── brands.json
│   ├── categories.json
│   └── default_products.json
│
├── scripts/               # Вспомогательные скрипты
│   ├── bootstrap_database.py   # Инициализация БД
│   ├── generate_test_data.py   # Генерация тестовых данных
│   ├── import_products.py      # Импорт каталога продуктов
│   └── rebuild_gtin_index.py   # Перестроение индекса GTIN
│
├── tests/                 # Тесты
│   ├── img/               # Изображения для тестов
│   └── test_api.py        # API тесты
│
├── infrastructure/        # Инфраструктура
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.bot
│   ├── env.example
│   └── monitoring/
│
├── docs/                  # Документация
│   ├── API_SPEC.md
│   ├── API_CONTRACTS.md
│   ├── ARCHITECTURE_DECISIONS.md
│   ├── BOT_DIALOG_FLOW.md
│   ├── Bot_v_0-1.md
│   ├── Bot_v_1.md
│   ├── Bot_v_2.md
│   ├── CI_PIPELINE.md
│   ├── CODE_GENERATION_RULES.md
│   ├── DATABASE_SCHEMA.sql
│   ├── DATA_PIPELINES.md
│   ├── DOMAIN_MODEL.md
│   ├── EVENT_SCHEMA.md
│   ├── FRIDGE_ANALYTICS.md
│   ├── GTIN_IMPORT_PIPELINE.md
│   ├── IMAGE_PRODUCT_RECOGNITION.md
│   ├── MASTER_BUILD_PROMPT.md
│   ├── ML_PRODUCT_CLASSIFIER.md
│   ├── MODULE_TEMPLATES.md
│   ├── PERFORMANCE_SCALING.md
│   ├── PROJECT_ROADMAP.md
│   ├── RECEIPT_SCANNER.md
│   ├── RECIPE_ENGINE.md
│   ├── SCAN_PIPELINE.md
│   ├── SERVICE_DEPENDENCIES.md
│   ├── SHOPPING_LIST_ENGINE.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── TASK_QUEUE.md
│   ├── TEST_STRATEGY.md
│   └── UI_DIALOG_MAP.md
│
├── logs/                  # Логи
├── requirements.txt       # Python зависимости
├── pytest.ini            # Конфигурация тестов
└── KODA.md              # Этот файл
```

---

## Текущий статус разработки

### MVP v0.1 — Основные функции реализованы

**Работающие функции:**
- ✅ Регистрация пользователя (`/start`)
- ✅ Добавление продуктов вручную через диалог (`/add`)
- ✅ Просмотр содержимого холодильника (`/fridge`)
- ✅ Удаление продуктов с указанием причины (used/expired/other)
- ✅ Просмотр истекающих продуктов (`/expiring`)
- ✅ Удаление просроченных продуктов
- ✅ Настройки уведомлений (включение/выключение, дни до, время)
- ✅ Сохранение настроек в базу данных
- ✅ Индикаторы статуса продуктов (❌ просрочен, ⚠️ истекает, ✅ свежий)
- ✅ Кнопка «Обновить» в просмотре холодильника

**Требуется доработка:**
- ⏳ Автоматическое создание пользователя при добавлении продукта
- ⏳ Worker для отправки уведомлений
- ⏳ Сканирование DataMatrix
- ⏳ Рекомендации рецептов
- ⏳ Список покупок

---

## Версии развития

### v0.1 — MVP (текущая)
- Ручное добавление продуктов
- Категории продуктов (11 категорий)
- Уведомления о сроке годности
- Просмотр содержимого холодильника
- Удаление продуктов с указанием причины
- Настройки уведомлений

### v1 — Сканирование DataMatrix
- Автоматическое распознавание по маркировке
- Извлечение GTIN и срока годности
- База продуктов и брендов
- Зоны холодильника
- Worker для обработки изображений

### v2 — Масштабируемая система
- База 1–2 млн GTIN
- ML классификация продуктов
- Рекомендации рецептов
- Семейный холодильник
- Аналитика использования
- Распознавание чеков (план)

---

## Запуск проекта

### Предварительная подготовка

1. **Копировать и настроить переменные окружения:**
```powershell
cd infrastructure
cp env.example .env
# Отредактировать .env — задать BOT_TOKEN, DATABASE_URL и др.
```

2. **Инициализировать базу данных:**
```powershell
cd scripts
python bootstrap_database.py
```

3. **Запустить сервисы:**
```powershell
cd infrastructure
docker-compose up -d
```

### Через Docker Compose

```powershell
cd infrastructure
cp env.example .env
# Отредактировать .env
docker-compose up -d
```

### Проверка подключения

```powershell
# Проверить работу API
curl http://localhost:8000/health

# Проверить подключение к БД
curl http://localhost:8000/api/v1/products/categories
```

### Сервисы в Docker

| Контейнер | Описание |
|-----------|----------|
| `fridge_postgres` | База данных PostgreSQL |
| `fridge_redis` | Кэш и очередь Redis |
| `fridge_api` | REST API |
| `fridge_bot` | Telegram бот |

---

## API Endpoints

### Базовый URL: `/api/v1`

**Важно:** Параметр `telegram_id` передаётся как **query-параметр** в URL, а не в теле запроса.

Пример: `POST /fridge/items?telegram_id=123456789`

**Пользователи:**
- `POST /users/register` — регистрация (telegram_id в теле)
- `GET /users/{telegram_id}` — информация о пользователе

**Холодильники:**
- `GET /fridges?telegram_id=...` — список холодильников
- `POST /fridges?telegram_id=...` — создание холодильника

**Продукты:**
- `GET /fridge/items?telegram_id=...` — список продуктов
- `POST /fridge/items?telegram_id=...` — добавить продукт
- `PATCH /fridge/items/{id}?telegram_id=...` — обновить продукт
- `DELETE /fridge/items/{id}?telegram_id=...&reason=...` — удалить продукт
- `POST /fridge/items/batch-delete?telegram_id=...&reason=...` — пакетное удаление
- `GET /fridge/expiring?telegram_id=...&days=...` — истекающие продукты

**Поиск:**
- `GET /products/search?q=` — поиск по названию
- `GET /products/gtin/{gtin}` — поиск по GTIN

**Сканирование:**
- `POST /scan/datamatrix` — сканирование DataMatrix

**Уведомления:**
- `GET /notifications/settings?telegram_id=...` — настройки
- `POST /notifications/settings?telegram_id=...` — обновить настройки

---

## Команды Telegram бота

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация пользователя |
| `/add` | Добавить продукт в холодильник |
| `/fridge` | Посмотреть содержимое холодильника |
| `/expiring` | Истекающие продукты |
| `/settings` | Настройки уведомлений |
| `/help` | Справка |

---

## Правила кодогенерации

### Язык и локализация

- **Код:** Английский
- **Комментарии:** Английский
- **Сообщения бота:** Русский
- **Документация:** Русский

**Пример:**

```python
# Good
async def get_expiring_products(days: int) -> list[FridgeItem]:
    """Return products expiring within specified days."""
    pass

# Bot messages
WELCOME_MESSAGE = "Добро пожаловать в Fridge Bot!"
EXPIRING_MESSAGE = "У вас есть продукты с истекающим сроком:"
```

### Асинхронность

Весь I/O код должен быть async:
- Database: SQLAlchemy async
- HTTP: httpx
- Telegram: aiogram

### Типизация

Все функции должны иметь type hints:

```python
async def add_fridge_item(
    fridge_id: int,
    product_id: int,
    quantity: int = 1,
    expiration_date: date | None = None
) -> FridgeItem:
    pass
```

### Тестирование

- Минимальное покрытие: **80%**
- Критические модули (scanner, database, API): **90%**

---

## Структура слоёв API

### Router → Service → Repository → Model

```
api/routers/          # Обработка HTTP запросов
    ↓
api/services/         # Бизнес-логика
    ↓
api/repositories/     # Доступ к данным
    ↓
api/models/           # SQLAlchemy модели
    ↓
api/database/         # Подключение к БД
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

## Кэширование в Redis

| Тип кэша | Key pattern | TTL |
|----------|-------------|-----|
| FSM State | `fsm:{user_id}:{key}` | сессия |
| GTIN Cache | `gtin:{gtin_code}` | 24 часа |
| Session Cache | `session:{telegram_id}` | 1 час |
| Task Queue | `celery:*` | - |

---

## Тестирование

```powershell
# Запуск всех тестов
pytest tests/

# Запуск с покрытием
pytest tests/ --cov=api --cov=bot

# Конкретный тест
pytest tests/test_api.py
```

---

## Диагностика

### Проверка работы сервисов

```powershell
# Статус Docker-контейнеров
docker-compose ps

# Логи бота
docker-compose logs -f bot

# Логи API
docker-compose logs -f api

# Логи базы данных
docker-compose logs -f postgres
```

### Проверка подключения к API

```powershell
# Health-check
curl http://localhost:8000/health

# Проверка категорий
curl http://localhost:8000/api/v1/products/categories

# Проверка регистрации пользователя
curl -X POST http://localhost:8000/api/v1/users/register `
  -H "Content-Type: application/json" `
  -d '{"telegram_id": 123456789}'
```

### Проверка базы данных

```powershell
# Подключение к PostgreSQL
docker-compose exec postgres psql -U postgres -d fridge_bot

# Проверка таблиц
\dt

# Проверка категорий
SELECT * FROM categories;
```

---

## Типичные проблемы и решения

### 1. Продукты не сохраняются в холодильник

**Причина:** Несоответствие формата передачи `telegram_id`.

**Решение:** API ожидает `telegram_id` как query-параметр:

```python
# ❌ Неправильно
await api_client.post("/fridge/items", {
    "telegram_id": user_id,
    "product_name": "Молоко"
})

# ✅ Правильно
await api_client.post(
    "/fridge/items",
    data={"product_name": "Молоко"},
    params={"telegram_id": user_id}
)
```

### 2. «Категории не найдены»

**Причина:** База данных не инициализирована.

**Решение:**
```powershell
python scripts/bootstrap_database.py
```

### 3. Бот не отвечает на команды

**Причины:**
- Неверный `BOT_TOKEN` — проверить в `.env`
- API недоступен — проверить `API_URL` в конфиге бота
- Бот не зарегистрирован у @BotFather

### 4. Ошибка подключения к базе данных

**Решение:**
```powershell
docker-compose ps postgres
docker-compose down -v
docker-compose up -d postgres
python scripts/bootstrap_database.py
```

### 5. Callback от бота вместо пользователя

**Проблема:** При обработке callback от inline-кнопки `callback.message.from_user` содержит данные бота, а не пользователя.

**Решение:** Использовать паттерн `FakeMessage`:

```python
class FakeMessage:
    def __init__(self, original_message, user_id):
        self._original = original_message
        self.from_user = type('obj', (object,), {'id': user_id})()
    
    def __getattr__(self, name):
        return getattr(self._original, name)
    
    async def answer(self, text, **kwargs):
        return await self._original.answer(text, **kwargs)
```

---

## Важные файлы документации

| Файл | Назначение |
|------|------------|
| `docs/PROJECT_ROADMAP.md` | План развития по фазам |
| `docs/TASK_QUEUE.md` | Очередь задач для агентов |
| `docs/CODE_GENERATION_RULES.md` | Правила генерации кода |
| `docs/SERVICE_DEPENDENCIES.md` | Зависимости между модулями |
| `docs/DATABASE_SCHEMA.sql` | Схема базы данных |
| `docs/API_SPEC.md` | Спецификация API |
| `docs/SCAN_PIPELINE.md` | Пайплайн сканирования |
| `docs/RECIPE_ENGINE.md` | Движок рецептов |
| `docs/SHOPPING_LIST_ENGINE.md` | Генератор списка покупок |

---

## Скрипты и утилиты

| Скрипт | Назначение |
|--------|------------|
| `scripts/bootstrap_database.py` | Инициализация БД, создание таблиц, seed-данные |
| `scripts/generate_test_data.py` | Генерация тестовых данных |
| `scripts/import_products.py` | Импорт каталога продуктов |
| `scripts/rebuild_gtin_index.py` | Перестроение индекса GTIN |

---

## ML модули

### Классификатор продуктов

- **Файл:** `ml/product_classifier/`
- **Назначение:** Автоматическое определение категории продукта по названию
- **Категории:** Молочные, Мясо, Рыба, Овощи, Фрукты, Напитки, Соусы, Заморозка, Хлеб, Снеки, Другое

### Движок рецептов

- **Файл:** `ml/recipe_engine/`
- **Назначение:** Подбор рецептов на основе имеющихся продуктов
- **Формула:** `score = matching_ingredients / total_ingredients`

### Генератор списка покупок

- **Файл:** `ml/shopping_engine/`
- **Назначение:** Автоматическая генерация списка покупок
- **Источники:** Истекающие продукты, недостающие ингредиенты для рецептов, частые покупки

---

## Импортеры данных

| Импортер | Назначение |
|----------|------------|
| `importers/gtin_importer.py` | Импорт GTIN кодов |
| `importers/openfoodfacts_importer.py` | Импорт из Open Food Facts |
| `importers/retail_catalog_importer.py` | Импорт из каталогов ритейлеров |

---

## Workers

| Worker | Назначение |
|--------|------------|
| `workers/scan_worker.py` | Обработка изображений и декодирование DataMatrix |
| `workers/notification_worker.py` | Проверка сроков годности и отправка уведомлений |
| `workers/import_worker.py` | Импорт GTIN каталогов |
| `workers/analytics_worker.py` | Сбор аналитики использования |

---

## Производительность

### Целевые показатели

| Метрика | Цель |
|---------|------|
| Время ответа API | < 100ms |
| Обработка скана | < 5s |
| Доставка уведомлений | < 10s |
| GTIN lookup | < 10ms |
| Одновременные пользователи | 1000+ |

---