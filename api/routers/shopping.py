"""API router for shopping list operations."""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Body

from ..schemas.shopping_schema import (
    ShoppingListResponse,
    ShoppingItemCreate,
    ShoppingItemUpdate,
    ShoppingItemResponse
)
from ..services.shopping_service import ShoppingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shopping", tags=["shopping"])


def get_shopping_service() -> ShoppingService:
    """Dependency injection for ShoppingService."""
    return ShoppingService()


@router.get("/list", response_model=ShoppingListResponse)
async def get_shopping_list(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    service: ShoppingService = Depends(get_shopping_service)
) -> ShoppingListResponse:
    """
    Get user's shopping list.

    Query params:
    - telegram_id: User's Telegram ID (required)

    Returns shopping list.
    """
    logger.info(f"Getting shopping list for user {telegram_id}")

    return await service.get_shopping_list(telegram_id)


@router.post("/items", response_model=ShoppingItemResponse, status_code=201)
async def add_shopping_item(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    data: ShoppingItemCreate = Body(...),
    service: ShoppingService = Depends(get_shopping_service)
) -> ShoppingItemResponse:
    """
    Add item to shopping list.

    Query params:
    - telegram_id: User's Telegram ID (required)

    Request body:
    - product_name: Product name (required)
    - quantity: Quantity (optional)
    - note: Note (optional)

    Returns created item.
    """
    logger.info(f"Adding shopping item for user {telegram_id}")

    return await service.add_item(telegram_id, data)


@router.patch("/items/{item_id}", response_model=ShoppingItemResponse)
async def update_shopping_item(
    item_id: int,
    telegram_id: int = Query(..., description="User's Telegram ID"),
    data: ShoppingItemUpdate = Body(...),
    service: ShoppingService = Depends(get_shopping_service)
) -> ShoppingItemResponse:
    """
    Update shopping list item.

    Path params:
    - item_id: Item ID

    Query params:
    - telegram_id: User's Telegram ID (required)

    Request body:
    - quantity: New quantity (optional)
    - purchased: Mark as purchased (optional)
    - note: New note (optional)

    Returns updated item.
    """
    logger.info(f"Updating shopping item {item_id}")

    result = await service.update_item(telegram_id, item_id, data)

    if not result:
        raise HTTPException(status_code=404, detail="Item not found")

    return result


@router.delete("/items/{item_id}")
async def delete_shopping_item(
    item_id: int,
    telegram_id: int = Query(..., description="User's Telegram ID"),
    service: ShoppingService = Depends(get_shopping_service)
) -> dict:
    """
    Delete item from shopping list.

    Path params:
    - item_id: Item ID

    Query params:
    - telegram_id: User's Telegram ID (required)

    Returns deletion status.
    """
    logger.info(f"Deleting shopping item {item_id}")

    deleted = await service.delete_item(telegram_id, item_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"deleted": True, "item_id": item_id}


@router.post("/generate")
async def generate_shopping_list(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    service: ShoppingService = Depends(get_shopping_service)
) -> ShoppingListResponse:
    """
    Auto-generate shopping list based on:
    - Expiring products
    - Frequently used products
    - Missing ingredients for recipes

    Query params:
    - telegram_id: User's Telegram ID (required)

    Returns generated shopping list.
    """
    logger.info(f"Generating shopping list for user {telegram_id}")

    return await service.generate_list(telegram_id)
