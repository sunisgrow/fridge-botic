# API Specification

Backend API for Fridge Telegram Bot.

Base URL: `/api/v1`

---

## Authentication

Authentication is based on Telegram ID.

Each request includes `telegram_id` in body or header.

---

## Endpoints

### Users

#### POST /users/register
Register a new user.

**Request:**
```json
{
  "telegram_id": 123456789,
  "username": "user123",
  "first_name": "Ivan"
}
```

**Response:**
```json
{
  "user_id": 1,
  "fridge_id": 1,
  "created": true
}
```

#### GET /users/{telegram_id}
Get user information.

**Response:**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "username": "user123",
  "fridges": [
    {
      "id": 1,
      "name": "Основной холодильник"
    }
  ],
  "notification_settings": {
    "enabled": true,
    "days_before": 3
  }
}
```

---

### Fridges

#### GET /fridges
Get user fridges.

**Query params:**
- `telegram_id` (required)

**Response:**
```json
{
  "fridges": [
    {
      "id": 1,
      "name": "Основной холодильник",
      "items_count": 15
    }
  ]
}
```

#### POST /fridges
Create new fridge.

**Request:**
```json
{
  "telegram_id": 123456789,
  "name": "Дача"
}
```

**Response:**
```json
{
  "id": 2,
  "name": "Дача",
  "created_at": "2025-01-15T10:00:00Z"
}
```

---

### Fridge Items

#### GET /fridge/items
Get all items in fridge.

**Query params:**
- `telegram_id` (required)
- `fridge_id` (optional)
- `category` (optional)
- `expiring_days` (optional)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "product_name": "Молоко 3.2%",
      "brand": "Простоквашино",
      "category": "Молочные продукты",
      "quantity": 2,
      "expiration_date": "2026-03-20",
      "days_until_expiry": 65,
      "added_at": "2025-01-15T10:00:00Z",
      "opened": false
    }
  ],
  "total": 1
}
```

#### POST /fridge/items
Add item to fridge.

**Request:**
```json
{
  "telegram_id": 123456789,
  "product_name": "Молоко 3.2%",
  "brand_name": "Простоквашино",
  "category_id": 1,
  "quantity": 2,
  "expiration_date": "2026-03-20",
  "zone_id": null
}
```

**Response:**
```json
{
  "id": 1,
  "product_name": "Молоко 3.2%",
  "category": "Молочные продукты",
  "quantity": 2,
  "expiration_date": "2026-03-20",
  "days_until_expiry": 65
}
```

#### PATCH /fridge/items/{id}
Update item.

**Request:**
```json
{
  "quantity": 1,
  "opened": true
}
```

#### DELETE /fridge/items/{id}
Remove item.

**Query params:**
- `telegram_id` (required)
- `reason` (optional): "used" | "expired" | "other"

---

### Products

#### GET /products/search
Search products by name.

**Query params:**
- `q` (required): search query
- `category_id` (optional)
- `limit` (default: 10)

**Response:**
```json
{
  "products": [
    {
      "id": 1,
      "name": "Молоко 3.2%",
      "brand": "Простоквашино",
      "category": "Молочные продукты",
      "default_shelf_life_days": 7
    }
  ]
}
```

#### GET /products/gtin/{gtin}
Lookup product by GTIN.

**Response:**
```json
{
  "product": {
    "id": 1,
    "name": "Молоко 3.2%",
    "brand": "Простоквашино",
    "category": "Молочные продукты"
  },
  "gtin": "04607062446630"
}
```

**404 Response:**
```json
{
  "error": "product_not_found",
  "gtin": "04607062446630"
}
```

#### POST /products
Create new product.

**Request:**
```json
{
  "name": "Новый продукт",
  "brand_name": "Бренд",
  "category_id": 1,
  "gtin": "04607062446630",
  "default_shelf_life_days": 14
}
```

---

### Categories

#### GET /categories
Get all categories.

**Response:**
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Молочные продукты",
      "icon": "🥛"
    },
    {
      "id": 2,
      "name": "Мясо",
      "icon": "🥩"
    }
  ]
}
```

---

### Brands

#### GET /brands/search
Search brands.

**Query params:**
- `q` (required)

**Response:**
```json
{
  "brands": [
    {
      "id": 1,
      "name": "Простоквашино",
      "country": "Russia"
    }
  ]
}
```

---

### Scan

#### POST /scan/datamatrix
Scan DataMatrix from image.

**Request:**
```json
{
  "telegram_id": 123456789,
  "image_file_id": "AgACAgIAAxkBAAI..."
}
```

**Response (success):**
```json
{
  "success": true,
  "gtin": "04607062446630",
  "product": {
    "id": 1,
    "name": "Молоко 3.2%",
    "brand": "Простоквашино",
    "category": "Молочные продукты"
  },
  "expiration_date": "2026-03-20",
  "raw_code": "0104607062446630..."
}
```

**Response (product not found):**
```json
{
  "success": true,
  "gtin": "04607062446630",
  "product": null,
  "expiration_date": "2026-03-20",
  "message": "Product not found in database"
}
```

**Response (scan failed):**
```json
{
  "success": false,
  "error": "no_code_detected",
  "message": "Could not detect DataMatrix in image"
}
```

---

### Notifications

#### GET /notifications/settings
Get notification settings.

**Query params:**
- `telegram_id` (required)

**Response:**
```json
{
  "enabled": true,
  "days_before": 3,
  "notification_time": "09:00:00"
}
```

#### PUT /notifications/settings
Update notification settings.

**Request:**
```json
{
  "telegram_id": 123456789,
  "enabled": true,
  "days_before": 5,
  "notification_time": "10:00:00"
}
```

#### GET /notifications/pending
Get pending notifications.

**Query params:**
- `telegram_id` (required)

**Response:**
```json
{
  "notifications": [
    {
      "id": 1,
      "product_name": "Молоко 3.2%",
      "expiration_date": "2025-01-18",
      "days_until_expiry": 3
    }
  ]
}
```

---

### Recipes

#### GET /recipes
Get recipe recommendations.

**Query params:**
- `telegram_id` (required)
- `limit` (default: 5)

**Response:**
```json
{
  "recipes": [
    {
      "id": 1,
      "name": "Омлет с овощами",
      "cooking_time_minutes": 15,
      "match_score": 0.85,
      "available_ingredients": [
        {"name": "яйца", "available": true},
        {"name": "молоко", "available": true},
        {"name": "помидоры", "available": true},
        {"name": "зелень", "available": false}
      ]
    }
  ]
}
```

#### GET /recipes/{id}
Get recipe details.

**Response:**
```json
{
  "id": 1,
  "name": "Омлет с овощами",
  "description": "Быстрый завтрак",
  "instructions": "1. Взбейте яйца...",
  "cooking_time_minutes": 15,
  "servings": 2,
  "ingredients": [
    {"name": "яйца", "quantity": "3 шт"},
    {"name": "молоко", "quantity": "100 мл"},
    {"name": "помидоры", "quantity": "2 шт"},
    {"name": "зелень", "quantity": "по вкусу"}
  ]
}
```

---

### Shopping List

#### GET /shopping
Get shopping list.

**Query params:**
- `telegram_id` (required)

**Response:**
```json
{
  "list": {
    "id": 1,
    "items": [
      {
        "id": 1,
        "product_name": "Молоко 3.2%",
        "quantity": 1,
        "is_purchased": false,
        "reason": "expiring_soon"
      }
    ]
  }
}
```

#### POST /shopping/items
Add item to shopping list.

**Request:**
```json
{
  "telegram_id": 123456789,
  "product_name": "Хлеб",
  "quantity": 1
}
```

#### PATCH /shopping/items/{id}
Mark item as purchased.

**Request:**
```json
{
  "is_purchased": true
}
```

#### DELETE /shopping/items/{id}
Remove item from list.

---

### Health

#### GET /health
Health check.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-01-15T10:00:00Z"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "error_code",
  "message": "Human readable message",
  "details": {}
}
```

Common error codes:
- `validation_error` - Invalid input
- `not_found` - Resource not found
- `unauthorized` - Invalid telegram_id
- `rate_limited` - Too many requests
- `internal_error` - Server error