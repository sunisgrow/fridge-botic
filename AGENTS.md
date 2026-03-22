# AGENTS.md - Guidelines for AI Coding Agents

## Project Overview

Fridge Bot is a Telegram bot for managing fridge inventory with the following features:
- Add/view/delete products from fridge
- Track expiration dates
- Scan DataMatrix/EAN barcodes via Mini App
- Manual product entry
- Notifications for expiring products

**Tech Stack:**
- **Backend:** FastAPI 0.109, SQLAlchemy 2.0 (async), PostgreSQL, Redis
- **Bot:** aiogram 3.4.1 (Telegram Bot Framework)
- **Scanner:** html5-qrcode, ZXing, OpenCV
- **Deployment:** Docker, Docker Compose

---

## Build/Lint/Test Commands

### Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_bot_handlers.py

# Run specific test by name
pytest tests/test_bot_handlers.py::TestStartHandler::test_start_command_registers_user

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=api --cov=bot --cov=scanner
```

### Code Quality
```bash
# Format code (Black)
black .

# Lint code (Flake8)
flake8 .

# Type checking (MyPy)
mypy .

# All checks before commit
black . && flake8 . && mypy .
```

### Docker
```bash
# Build and start all services
cd infrastructure && docker-compose up -d --build

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart bot

# Stop all services
docker-compose down
```

---

## Code Style Guidelines

### Import Organization
```python
# 1. Standard library
import json
import logging
from datetime import datetime, date
from typing import Optional, List, Dict

# 2. Third-party packages
from aiogram import Router, F
from fastapi import APIRouter, Depends
from sqlalchemy import select

# 3. Local imports (relative)
from ..services.api_client import APIClient
from ..keyboards.main_menu import get_main_keyboard
```

### Type Hints
- **Required** for all function parameters and return types
- Use `Optional[X]` instead of `X | None`
- Use `List[X]`, `Dict[K, V]` instead of `list[X]`, `dict[K, V]`
```python
async def get_categories(self) -> list[dict]:
    ...

async def process_webapp_data(
    callback: CallbackQuery,
    state: FSMContext,
    api_client: APIClient
) -> None:
    ...
```

### Docstrings
Use Google-style docstrings:
```python
async def lookup_product(
    telegram_id: int,
    gtin: str,
    raw_data: Optional[str] = None
) -> dict:
    """
    Lookup product by GTIN code.

    Args:
        telegram_id: User's Telegram ID
        gtin: GTIN/EAN barcode code
        raw_data: Raw barcode data (optional)

    Returns:
        Dict with product info or error message

    Raises:
        httpx.HTTPStatusError: On API error
    """
```

### Naming Conventions
| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `api_client.py` |
| Classes | PascalCase | `APIClient` |
| Functions | snake_case | `get_categories` |
| Constants | UPPER_SNAKE | `MAX_QUANTITY` |
| Private | _leading | `_get_session` |
| Types | PascalCase | `UserResponse` |

### Async/Await Patterns
```python
# CORRECT - async context manager
async with get_session() as session:
    result = await session.execute(query)

# CORRECT - dependency injection
def get_service() -> Service:
    return Service()

@router.get("/items")
async def get_items(service: Service = Depends(get_service)):
    ...

# WRONG - blocking in async
def sync_function():
    data = requests.get(url)  # Use httpx instead!
```

### Error Handling
```python
# Use specific exceptions
try:
    result = await api_client.lookup(gtin)
except httpx.HTTPStatusError as e:
    logger.error(f"API error: {e}")
    raise HTTPException(status_code=500, detail=str(e))

# Always catch and log exceptions in handlers
try:
    await callback.message.answer(text)
except Exception as e:
    logger.error(f"Error sending message: {e}", exc_info=True)
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug("Detailed debug info")
logger.info("User action: {telegram_id}")
logger.warning("Retry attempt {attempt}")
logger.error(f"Failed to process: {e}", exc_info=True)
```

---

## Project Structure

```
fridge-botic/
├── api/                    # FastAPI backend
│   ├── main.py            # FastAPI app entry point
│   ├── config.py          # Settings from environment
│   ├── database/          # Database session management
│   │   └── session.py     # SQLAlchemy async session
│   ├── models/            # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── fridge.py
│   │   └── category.py
│   ├── repositories/      # Data access layer
│   ├── routers/          # API endpoints
│   │   ├── users.py       # POST /users/register
│   │   ├── fridge.py      # GET/POST /fridge/items
│   │   ├── products.py    # GET /products/categories
│   │   └── scan.py        # POST /scan/webapp
│   ├── schemas/          # Pydantic models
│   └── services/         # Business logic
│
├── bot/                   # Telegram bot (aiogram)
│   ├── main.py           # Bot entry point
│   ├── config.py         # Bot settings
│   ├── handlers/         # Message/callback handlers
│   │   ├── start.py
│   │   ├── add_product.py
│   │   ├── scan_product.py
│   │   ├── fridge_view.py
│   │   └── expiring_products.py
│   ├── keyboards/        # Inline/Reply keyboards
│   │   ├── main_menu.py
│   │   ├── categories.py
│   │   └── scan_keyboard.py
│   └── services/        # Bot API client
│       └── api_client.py
│
├── scanner/              # Barcode/DataMatrix processing
│   ├── gs1_parser.py    # GS1 barcode format parser
│   ├── datamatrix_decoder.py
│   └── image_preprocessing.py
│
├── webapp/               # Telegram Mini App
│   ├── index.html
│   ├── app.js            # Scanner logic
│   └── style.css
│
├── infrastructure/       # Docker deployment
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.bot
│   └── .env.example
│
├── tests/                # Pytest tests
│   ├── test_bot_handlers.py
│   ├── test_bot_api_client.py
│   ├── test_api.py
│   └── test_scanner.py
│
├── data/                 # Seed data
│   ├── categories.json
│   └── default_products.json
│
├── requirements.txt      # Dev dependencies
├── requirements-prod.txt # Production dependencies
├── pytest.ini            # Pytest config
└── README.md
```

---

## Key Patterns

### FSM (Finite State Machine) for Bot
```python
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class AddProductState(StatesGroup):
    name = State()
    category = State()
    quantity = State()
    expiration = State()

@router.message(AddProductState.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(product_name=message.text)
    await state.set_state(AddProductState.category)
```

### API Router Pattern
```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/fridge", tags=["fridge"])

def get_fridge_service() -> FridgeService:
    return FridgeService()

@router.get("/items")
async def get_items(
    telegram_id: int = Query(...),
    service: FridgeService = Depends(get_fridge_service)
) -> FridgeResponse:
    return await service.get_items(telegram_id)
```

### Database Session
```python
from api.database.session import get_session

async def get_items(telegram_id: int) -> List[Item]:
    async with get_session() as session:
        result = await session.execute(
            select(Item).where(Item.telegram_id == telegram_id)
        )
        return list(result.scalars().all())
```

---

## Important Notes

### WebApp Data Handling
When using Telegram Mini App with InlineKeyboardButton:
- Mini App opens via WebApp button
- `tg.sendData()` sends data back to bot
- In aiogram 3.x, use `@router.message(F.web_app_data)` for KeyboardButton
- For InlineKeyboardButton, data comes via `callback_query.data`

### Redis for FSM
The bot uses Redis for FSM storage (state persistence):
- Configured in `bot/config.py` via `REDIS_URL`
- Falls back to MemoryStorage if Redis unavailable
- Ensure Redis is running in Docker environment

### Docker Ports
| Service | Internal | External |
|---------|----------|----------|
| API | 8000 | 8000 or 8443 |
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |

### Environment Variables
Copy `.env.example` to `.env` in `infrastructure/`:
```bash
cp infrastructure/env.example infrastructure/.env
# Edit .env with your values
```
