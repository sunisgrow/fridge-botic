# Bot_v_1 — бот со сканированием Data Matrix

Эта версия добавляет автоматическое распознавание продуктов по маркировке.

Используется стандарт GS1 DataMatrix и маркировка системы "Честный знак".

---

# Новые функции

1. автоматическое добавление продуктов
2. сканирование DataMatrix
3. извлечение GTIN
4. автоматическое определение продукта
5. извлечение срока годности
6. библиотека брендов
7. библиотека продуктов
8. зоны холодильника

---

# Новый пользовательский сценарий

1 пользователь нажимает "Сканировать"
2 отправляет фото упаковки
3 бот распознаёт DataMatrix
4 извлекает GTIN
5 ищет товар в базе
6 автоматически добавляет продукт

---

# Алгоритм сканирования

image
↓
preprocessing
↓
decode DataMatrix
↓
parse GS1 fields
↓
extract GTIN
↓
lookup product
↓
create fridge item

---

# Структура DataMatrix

Основные Application Identifiers:

01 → GTIN  
21 → serial  
17 → expiration date  
10 → batch  

Пример строки:

010460706244663021ABC1234567891725021510BATCH01

---

# Извлечение срока годности

AI 17

формат:

YYMMDD

пример:

250115 → 2025-01-15

---

# Обработка изображения

pipeline:

image
↓
grayscale
↓
noise reduction
↓
contrast enhancement
↓
adaptive threshold
↓
decode

---

# База продуктов

Добавляется таблица:

brands
- id
- name

product_gtins
- id
- product_id
- gtin

datamatrix_codes
- id
- gtin
- serial
- batch
- expiration_date
- raw_code

scan_logs
- id
- user_id
- datamatrix_id
- scanned_at

---

# Если GTIN не найден

бот спрашивает пользователя:

"Введите название продукта"

После этого:

INSERT product  
INSERT GTIN

База постепенно растёт.

---

# Архитектура

Telegram
↓
Bot
↓
API
↓
Queue (Redis)
↓
Scan Worker
↓
Database

---

# Worker задачи

scan_worker

- обработка изображений
- декодирование DataMatrix

notification_worker

- проверка сроков годности

---

# Цель версии

автоматическое добавление большинства продуктов через сканирование.