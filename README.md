# Fridge Bot — Telegram бот для управления продуктами

Telegram-бот для учёта продуктов в холодильнике с поддержкой сканирования DataMatrix кодов (Честный знак), отслеживания сроков годности и автоматических уведомлений.

## Возможности

### Сканирование DataMatrix
- Сканирование кодов с упаковок товаров
- Автоматическое определение товара по GTIN
- Поддержка российской маркировки (Честный знак)

### Управление холодильником
- Ручное добавление продуктов
- Выбор способа добавления: сканирование или вручную
- 11 категорий продуктов
- Просмотр содержимого с фильтрацией
- Удаление с указанием причины

### Сроки годности
- Уведомления о истекающих продуктах
- Настраиваемые оповещения (дни до, время)

## Технологии

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI |
| Bot | aiogram 3.x |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| ORM | SQLAlchemy 2.0 (async) |
| Scanner | OpenCV + zxing-cpp |
| ML | scikit-learn |

## Быстрый старт

### Docker Compose

```bash
cd infrastructure
cp env.example .env
# Отредактируйте .env - укажите TELEGRAM_BOT_TOKEN

docker-compose up -d
docker-compose exec api python scripts/bootstrap_database.py
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Регистрация пользователя |
| `/add` или кнопка **➕ Добавить** | Добавить продукт |
| **📷 Сканировать** | Сканировать DataMatrix |
| **✏️ Вручную** | Добавить вручную |
| `/fridge` или кнопка **📋 Холодильник** | Просмотр содержимого |
| `/scan` | Сканировать DataMatrix |
| `/expiring` | Истекающие продукты |
| `/settings` | Настройки уведомлений |

## Как добавить продукт

### Способ 1: Сканирование (рекомендуемый)

1. Нажмите **➕ Добавить**
2. Выберите **📷 Сканировать**
3. Отправьте фото DataMatrix кода с упаковки
4. Подтвердите или измените данные (количество, срок годности)
5. Продукт добавлен в холодильник

### Способ 2: Вручную

1. Нажмите **➕ Добавить**
2. Выберите **✏️ Вручную**
3. Введите название продукта
4. Выберите категорию (опционально)
5. Укажите количество
6. Введите срок годности (ДД.ММ.ГГГГ или количество дней)

## Тестовые данные

В базе данных预先 загружены тестовые GTIN:

| GTIN | Товар | Категория | Бренд |
|------|-------|-----------|-------|
| 04607163091577 | Молоко 3.2% | Молочные | Домик в деревне |
| 04600605034156 | Кефир 1% | Молочные | Простоквашино |
| 04607004891694 | Сметана 20% | Молочные | Тёма |

## API Endpoints

### Сканирование
- `POST /api/v1/scan/datamatrix` — Сканировать DataMatrix код

### Пользователи
- `POST /api/v1/users/register` — Регистрация
- `GET /api/v1/users/{telegram_id}` — Информация о пользователе

### Холодильник
- `GET /api/v1/fridge/items` — Список продуктов
- `POST /api/v1/fridge/items` — Добавить продукт
- `PATCH /api/v1/fridge/items/{id}` — Обновить продукт
- `DELETE /api/v1/fridge/items/{id}` — Удалить продукт
- `GET /api/v1/fridge/expiring` — Истекающие продукты

### Продукты
- `GET /api/v1/products/categories` — Категории
- `GET /api/v1/products/search?q=` — Поиск по названию
- `GET /api/v1/products/gtin/{gtin}` — Поиск по GTIN

### Уведомления
- `GET /api/v1/notifications/settings` — Настройки
- `POST /api/v1/notifications/settings` — Обновить настройки

## Структура проекта

```
fridge-bot/
├── api/                    # REST API (FastAPI)
│   ├── models/            # SQLAlchemy модели
│   ├── repositories/      # Доступ к данным
│   ├── routers/           # API endpoints
│   ├── schemas/           # Pydantic схемы
│   └── services/           # Бизнес-логика
│
├── bot/                    # Telegram бот (aiogram)
│   ├── handlers/          # Обработчики команд
│   ├── keyboards/          # Клавиатуры
│   ├── services/           # API клиент
│   └── main.py            # Точка входа
│
├── scanner/               # Сканирование DataMatrix
│   ├── datamatrix_decoder.py
│   ├── gs1_parser.py
│   └── image_preprocessing.py
│
├── ml/                    # Machine Learning
│   ├── product_classifier/
│   ├── recipe_engine/
│   └── shopping_engine/
│
├── workers/               # Фоновые задачи
├── importers/            # Импорт данных
├── scripts/             # Скрипты
├── tests/                # Тесты
└── infrastructure/       # Docker
```

## Локальная разработка

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Запустить БД
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15
docker run -d -p 6379:6379 redis:7

# 3. Инициализировать БД
python scripts/bootstrap_database.py

# 4. Запустить API
python -m uvicorn api.main:app --reload

# 5. Запустить бота
python -m bot.main
```

## Тестирование

```bash
# Все тесты
pytest tests/

# С покрытием
pytest tests/ --cov=api --cov=bot
```

## Как добавить свои GTIN

### Способ 1: Через скрипт

Добавьте товары в `scripts/bootstrap_database.py`:

```python
test_products = [
    {
        "name": "Ваш товар",
        "category_id": 1,  # ID категории из categories.json
        "brand_name": "Ваш бренд",
        "gtin": "12345678901234",
        "default_shelf_life_days": 7
    },
]
```

Затем перезапустите:
```bash
docker-compose exec api python scripts/bootstrap_database.py
```

### Способ 2: Напрямую в БД

```bash
docker-compose exec postgres psql -U postgres -d fridge_bot

-- Добавить бренд
INSERT INTO brands (name) VALUES ('Бренд') RETURNING id;
-- Добавить товар
INSERT INTO products (name, category_id, brand_id, default_shelf_life_days) 
VALUES ('Товар', 1, <brand_id>, 7) RETURNING id;
-- Добавить GTIN
INSERT INTO product_gtins (product_id, gtin) VALUES (<product_id>, '12345678901234');
```

### Способ 3: Импорт из Open Food Facts

```bash
python scripts/import_products.py --source openfoodfacts --category 1
```

## Известные проблемы

### 1. Сканер не распознаёт DataMatrix

**Симптомы:** При сканировании возвращает "Код не найден"

**Решение:**
```bash
# Пересобрать контейнер API
docker-compose build --no-cache api
docker-compose up -d
```

### 2. Бот не отвечает на команды

**Причины:**
- Неверный `BOT_TOKEN` в .env
- API недоступен
- Бот не зарегистрирован у @BotFather

**Решение:**
```bash
# Проверить токен
docker logs fridge_bot | grep "Starting"

# Проверить подключение к API
curl http://localhost:8000/health
```

### 3. Ошибка подключения к БД

**Решение:**
```bash
docker-compose restart postgres
docker-compose exec api python scripts/bootstrap_database.py
```

### 4. Товар не находится по GTIN

**Причина:** GTIN не добавлен в базу

**Решение:** Добавьте GTIN одним из способов выше

## Диагностика

```bash
# Статус контейнеров
docker-compose ps

# Логи
docker-compose logs -f api
docker-compose logs -f bot
docker-compose logs -f postgres

# Проверка API
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/products/categories

# Подключение к БД
docker-compose exec postgres psql -U postgres -d fridge_bot
```

## Разработка

- **Код**: Python с type hints
- **Стиль**: Black + flake8
- **Язык сообщений**: Русский
- **Комментарии**: Английский

## Лицензия

MIT
