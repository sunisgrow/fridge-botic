# Project Roadmap

Полный план разработки Fridge Bot — Telegram-бота для учета продуктов в холодильнике с поддержкой сканирования DataMatrix из системы "Честный знак".

---

## Общая информация

**Название проекта:** Fridge Bot

**Цель:** Создать Telegram-бота для управления продуктами в холодильнике с автоматическим распознаванием через DataMatrix.

**Технологический стек:**
- Backend: Python, FastAPI
- Bot: aiogram 3.x
- Database: PostgreSQL
- Queue/Cache: Redis
- Workers: Celery / RQ
- Containerization: Docker

---

## Фазы разработки

### Фаза 0: Подготовка инфраструктуры

**Длительность:** 1-2 дня

**Задачи:**

1. Создать структуру репозитория
2. Настроить Docker Compose
3. Создать конфигурационные файлы
4. Настроить подключение к PostgreSQL
5. Настроить Redis

**Артефакты:**
- docker-compose.yml
- .env.example
- Dockerfile.*
- config.py файлы

**Критерий готовности:**
```
docker-compose up
→ все сервисы запущены
→ PostgreSQL доступна
→ Redis доступен
```

---

### Фаза 1: База данных

**Длительность:** 1 день

**Задачи:**

1. Создать схему БД по DATABASE_SCHEMA.sql
2. Настроить SQLAlchemy модели
3. Создать миграции (Alembic)
4. Добавить seed данные (категории, бренды)

**Артефакты:**
- database/session.py
- database/base.py
- models/*.py
- migrations/
- data/categories.json
- data/brands.json

**Критерий готовности:**
```
Таблицы созданы
Модели работают
Seed данные загружены
```

---

### Фаза 2: API Backend (Core)

**Длительность:** 2-3 дня

**Задачи:**

1. Создать FastAPI приложение
2. Реализовать routers:
   - users.py
   - products.py
   - fridge.py
3. Реализовать services:
   - product_service.py
   - fridge_service.py
4. Реализовать repositories:
   - user_repo.py
   - product_repo.py
   - fridge_repo.py

**Артефакты:**
- api/main.py
- api/routers/*.py
- api/services/*.py
- api/repositories/*.py
- api/schemas/*.py

**API Endpoints (Phase 1):**

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | /users/register | Регистрация пользователя |
| GET | /users/{telegram_id} | Информация о пользователе |
| GET | /fridges | Список холодильников |
| POST | /fridges | Создать холодильник |
| GET | /fridge/items | Список продуктов |
| POST | /fridge/items | Добавить продукт |
| DELETE | /fridge/items/{id} | Удалить продукт |
| GET | /products/search | Поиск продукта |
| POST | /products | Создать продукт |

**Критерий готовности:**
```
API запущен на порту 8000
Swagger UI доступен
Все endpoints отвечают
```

---

### Фаза 3: Telegram Bot (MVP)

**Длительность:** 2-3 дня

**Задачи:**

1. Создать aiogram bot
2. Реализовать handlers:
   - start.py
   - add_product.py
   - fridge_view.py
   - expiring_products.py
   - settings.py
3. Реализовать keyboards:
   - main_menu.py
   - categories.py
   - confirmation.py
4. Реализовать FSM states:
   - add_product_state.py
5. Интегрировать с API

**Артефакты:**
- bot/main.py
- bot/handlers/*.py
- bot/keyboards/*.py
- bot/states/*.py
- bot/services/api_client.py

**Команды бота (Phase 1):**

| Команда | Описание |
|---------|----------|
| /start | Регистрация |
| /add | Добавить продукт |
| /fridge | Просмотр холодильника |
| /remove | Удалить продукт |
| /expiring | Истекающие продукты |
| /settings | Настройки |

**Критерий готовности:**
```
Bot отвечает на команды
Продукты добавляются
Холодильник отображается
```

---

### Фаза 4: Система уведомлений

**Длительность:** 1-2 дня

**Задачи:**

1. Создать notification_worker
2. Реализовать scheduler (APScheduler)
3. Добавить notification_settings endpoint
4. Интегрировать уведомления в bot

**Артефакты:**
- workers/notification_worker.py
- api/routers/notifications.py
- api/services/notification_service.py

**Алгоритм уведомлений:**

```
Каждый день в 09:00:
1. Найти продукты с expiration_date <= today + N дней
2. Отправить уведомление пользователю
3. Записать в notification_queue
```

**Критерий готовности:**
```
Уведомления отправляются
Настройки работают
Логи записываются
```

---

### Фаза 5: Сканирование DataMatrix

**Длительность:** 3-4 дня

**Задачи:**

1. Создать scanner модуль:
   - datamatrix_decoder.py
   - image_preprocessing.py
   - gs1_parser.py
2. Создать scan_worker
3. Реализовать scan API endpoint
4. Добавить scan handler в bot
5. Настроить очередь задач

**Артефакты:**
- scanner/datamatrix_decoder.py
- scanner/image_preprocessing.py
- scanner/gs1_parser.py
- workers/scan_worker.py
- api/routers/scan.py
- api/services/scan_service.py
- bot/handlers/scan_product.py

**Pipeline сканирования:**

```
photo → preprocessing → decode → parse GS1 → GTIN lookup → create item
```

**Критерий готовности:**
```
Фото обрабатывается
DataMatrix декодируется
GTIN извлекается
Продукт создаётся
```

---

### Фаза 6: База GTIN

**Длительность:** 2 дня

**Задачи:**

1. Создать importers модуль:
   - gtin_importer.py
   - openfoodfacts_importer.py
2. Создать import_worker
3. Загрузить начальный датасет
4. Создать индексы

**Артефакты:**
- importers/gtin_importer.py
- importers/openfoodfacts_importer.py
- workers/import_worker.py
- scripts/import_products.py

**Источники данных:**
- Open Food Facts (~2M товаров)
- Пользовательские GTIN

**Критерий готовности:**
```
1M+ GTIN в базе
Lookup < 10ms
Индексы работают
```

---

### Фаза 7: ML Классификатор продуктов

**Длительность:** 2-3 дня

**Задачи:**

1. Собрать датасет для обучения
2. Обучить модель классификации
3. Создать inference модуль
4. Интегрировать в product_service

**Артефакты:**
- ml/product_classifier/train_model.py
- ml/product_classifier/model.py
- ml/product_classifier/inference.py
- ml/models/product_classifier.bin

**Категории:**
- Dairy (Молочные)
- Meat (Мясо)
- Vegetables (Овощи)
- Fruits (Фрукты)
- Drinks (Напитки)
- Frozen (Заморозка)
- Snacks (Снеки)
- Sauces (Соусы)

**Критерий готовности:**
```
Accuracy > 85%
Inference < 50ms
```

---

### Фаза 8: Движок рецептов

**Длительность:** 2-3 дня

**Задачи:**

1. Создать data/recipes_dataset.json
2. Реализовать recipe_matcher
3. Реализовать recipe_ranker
4. Создать API endpoints
5. Добавить handler в bot

**Артефакты:**
- recipe_engine/recipe_matcher.py
- recipe_engine/recipe_ranker.py
- api/routers/recipes.py
- api/services/recipe_service.py
- bot/handlers/recipes.py
- data/recipes_dataset.json

**Алгоритм:**

```
fridge_items → extract ingredients → match recipes → score → rank → top 5
```

**Критерий готовности:**
```
Рецепты предлагаются
Matching работает
Рейтинг корректный
```

---

### Фаза 9: Список покупок

**Длительность:** 1-2 дня

**Задачи:**

1. Реализовать list_generator
2. Реализовать purchase_predictor
3. Создать API endpoints
4. Добавить handler в bot

**Артефакты:**
- shopping_engine/list_generator.py
- shopping_engine/purchase_predictor.py
- api/routers/shopping.py
- api/services/shopping_service.py
- bot/handlers/shopping_list.py

**Источники списка:**
- Истекающие продукты
- Рецепты (требуемые ингредиенты)
- Частые покупки

**Критерий готовности:**
```
Список генерируется
Пользователь видит предложения
```

---

### Фаза 10: Аналитика

**Длительность:** 2 дня

**Задачи:**

1. Создать analytics_worker
2. Реализовать метрики:
   - Часто портящиеся продукты
   - Объём выброшенной еды
   - Прогноз покупок
3. Создать API endpoints
4. Добавить handler в bot

**Артефакты:**
- workers/analytics_worker.py
- api/routers/analytics.py
- bot/handlers/analytics.py

**Метрики:**
- products_wasted (выброшено)
- products_used (использовано)
- expiration_rate (% просрочки)
- top_categories (популярные категории)

**Критерий готовности:**
```
Метрики считаются
Отчёты доступны
```

---

## Суммарная длительность

| Фаза | Длительность |
|------|--------------|
| 0. Infrastructure | 1-2 дня |
| 1. Database | 1 день |
| 2. API Core | 2-3 дня |
| 3. Bot MVP | 2-3 дня |
| 4. Notifications | 1-2 дня |
| 5. DataMatrix Scan | 3-4 дня |
| 6. GTIN Database | 2 дня |
| 7. ML Classifier | 2-3 дня |
| 8. Recipe Engine | 2-3 дня |
| 9. Shopping List | 1-2 дня |
| 10. Analytics | 2 дня |
| **Итого** | **19-27 дней** |

---

## Приоритеты MVP

Для минимальной рабочей версии необходимы:

1. **Фаза 0-3** (обязательно)
   - Infrastructure
   - Database
   - API Core
   - Bot MVP

2. **Фаза 4-5** (важно)
   - Notifications
   - DataMatrix Scan

3. **Фаза 6-10** (улучшения)
   - GTIN Database
   - ML Classifier
   - Recipe Engine
   - Shopping List
   - Analytics

---

## Зависимости между фазами

```
Phase 0 (Infrastructure)
    ↓
Phase 1 (Database)
    ↓
Phase 2 (API Core)
    ↓
Phase 3 (Bot MVP)
    ↓
┌───┴───┐
↓       ↓
Phase 4 Phase 5
(Notify) (Scan)
    ↓       ↓
    └───┬───┘
        ↓
    Phase 6 (GTIN DB)
        ↓
    Phase 7 (ML)
        ↓
┌───────┴───────┐
↓               ↓
Phase 8     Phase 9
(Recipes)   (Shopping)
    ↓           ↓
    └─────┬─────┘
          ↓
      Phase 10 (Analytics)
```

---

## Точки интеграции

### Bot ↔ API

Bot вызывает API через HTTP client:

```python
# bot/services/api_client.py
async def add_product(telegram_id, product_data):
    response = await http_client.post(
        f"{API_URL}/fridge/items",
        json={"telegram_id": telegram_id, **product_data}
    )
    return response.json()
```

### API ↔ Database

API использует repositories:

```python
# api/repositories/fridge_repo.py
async def add_item(fridge_id, product_id, expiration_date):
    item = FridgeItem(
        fridge_id=fridge_id,
        product_id=product_id,
        expiration_date=expiration_date
    )
    session.add(item)
    await session.commit()
    return item
```

### Workers ↔ Queue

Workers получают задачи из Redis:

```python
# workers/scan_worker.py
@celery.task
def process_scan(image_file_id):
    # download image
    # preprocess
    # decode
    # return result
```

---

## Контрольные точки

### Checkpoint 1: MVP Ready

После фазы 3:
- Bot работает
- Продукты добавляются
- Холодильник отображается

### Checkpoint 2: Smart Features

После фазы 5:
- Скан работает
- Уведомления работают
- GTIN распознаются

### Checkpoint 3: AI Features

После фазы 8:
- Рецепты предлагаются
- Список покупок генерируется
- Аналитика работает

---

## Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Плохое качество фото | Высокая | Среднее | Preprocessing pipeline |
| Нет GTIN в базе | Средняя | Низкое | Ручной ввод + ML классификация |
| Telegram API limits | Низкая | Среднее | Rate limiting, очереди |
| Большой размер БД | Средняя | Низкое | Индексы, партиционирование |