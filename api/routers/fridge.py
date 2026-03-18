"""API router for fridge operations."""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from ..schemas.fridge_schema import (
    FridgeItemCreate,
    FridgeItemUpdate,
    FridgeItemDelete,
    FridgeItemResponse,
    FridgeItemListResponse,
    FridgeCreate,
    FridgeResponse,
    FridgeListResponse,
    DeleteReason
)
from ..services.fridge_service import FridgeService
from ..repositories.fridge_repo import FridgeRepository
from ..repositories.product_repo import ProductRepository
from ..repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fridge", tags=["fridge"])


def get_fridge_service() -> FridgeService:
    """Dependency injection for FridgeService."""
    return FridgeService(
        fridge_repo=FridgeRepository(),
        product_repo=ProductRepository(),
        user_repo=UserRepository()
    )


@router.get("/items", response_model=FridgeItemListResponse)
async def get_fridge_items(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    expiring_days: Optional[int] = Query(None, description="Filter expiring within N days"),
    service: FridgeService = Depends(get_fridge_service)
) -> FridgeItemListResponse:
    """
    Get all items in user's fridge.

    Query params:
    - telegram_id: User's Telegram ID (required)
    - category_id: Filter by category (optional)
    - expiring_days: Show only items expiring within N days (optional)

    Returns list of fridge items with product details.
    """
    logger.info(f"Getting fridge items for user {telegram_id}")

    return await service.get_user_fridge_items(
        telegram_id,
        category_id=category_id,
        expiring_days=expiring_days
    )


@router.post("/items", response_model=FridgeItemResponse, status_code=201)
async def add_fridge_item(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    data: FridgeItemCreate = Body(...),
    service: FridgeService = Depends(get_fridge_service)
) -> FridgeItemResponse:
    """
    Add item to fridge.

    Query params:
    - telegram_id: User's Telegram ID (required)

    Request body:
    - product_name: Product name (required)
    - category_id: Category ID (optional)
    - brand_name: Brand name (optional)
    - quantity: Quantity (default: 1)
    - expiration_date: Expiration date in YYYY-MM-DD format (optional)
    - zone_id: Storage zone ID (optional)
    - opened: Whether item is opened (default: false)
    - note: Custom note (optional)

    Returns created fridge item.
    """
    logger.info(f"Adding item {data.product_name} for user {telegram_id}")

    try:
        return await service.add_fridge_item(telegram_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add item: {e}")
        raise HTTPException(status_code=500, detail="Failed to add item")


@router.patch("/items/{item_id}", response_model=FridgeItemResponse)
async def update_fridge_item(
    item_id: int,
    telegram_id: int = Query(..., description="User's Telegram ID"),
    data: FridgeItemUpdate = Body(...),
    service: FridgeService = Depends(get_fridge_service)
) -> FridgeItemResponse:
    """
    Update fridge item.

    Path params:
    - item_id: Item ID

    Query params:
    - telegram_id: User's Telegram ID (required)

    Request body:
    - quantity: New quantity (optional)
    - expiration_date: New expiration date (optional)
    - opened: New opened status (optional)
    - note: New note (optional)

    Returns updated fridge item.
    """
    logger.info(f"Updating item {item_id} for user {telegram_id}")

    result = await service.update_fridge_item(telegram_id, item_id, data)

    if not result:
        raise HTTPException(status_code=404, detail="Item not found")

    return result


@router.delete("/items/{item_id}")
async def delete_fridge_item(
    item_id: int,
    telegram_id: int = Query(..., description="User's Telegram ID"),
    reason: Optional[DeleteReason] = Query(None, description="Deletion reason"),
    service: FridgeService = Depends(get_fridge_service)
) -> dict:
    """
    Delete fridge item.

    Path params:
    - item_id: Item ID

    Query params:
    - telegram_id: User's Telegram ID (required)
    - reason: Deletion reason: used, expired, other (optional)

    Returns deletion status.
    """
    logger.info(f"Deleting item {item_id} for user {telegram_id}, reason: {reason}")

    deleted = await service.delete_fridge_item(telegram_id, item_id, reason)

    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")

    return {
        "deleted": True,
        "item_id": item_id,
        "reason": reason
    }


@router.post("/items/batch-delete")
async def batch_delete_fridge_items(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    reason: Optional[DeleteReason] = Query(None, description="Deletion reason"),
    item_ids: List[int] = Body(..., description="List of item IDs to delete"),
    service: FridgeService = Depends(get_fridge_service)
) -> dict:
    """
    Batch delete fridge items.

    Query params:
    - telegram_id: User's Telegram ID (required)
    - reason: Deletion reason: used, expired, other (optional)

    Request body:
    - List of item IDs to delete

    Returns deletion results.
    """
    logger.info(f"Batch deleting {len(item_ids)} items for user {telegram_id}")

    deleted_ids = []
    failed_ids = []

    for item_id in item_ids:
        deleted = await service.delete_fridge_item(telegram_id, item_id, reason)
        if deleted:
            deleted_ids.append(item_id)
        else:
            failed_ids.append(item_id)

    return {
        "deleted_count": len(deleted_ids),
        "deleted_ids": deleted_ids,
        "failed_ids": failed_ids,
        "reason": reason
    }


@router.get("/expiring", response_model=FridgeItemListResponse)
async def get_expiring_items(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    days: int = Query(3, description="Days threshold", ge=1, le=30),
    service: FridgeService = Depends(get_fridge_service)
) -> FridgeItemListResponse:
    """
    Get items expiring within specified days.

    Query params:
    - telegram_id: User's Telegram ID (required)
    - days: Days threshold (default: 3, range: 1-30)

    Returns list of expiring items.
    """
    logger.info(f"Getting expiring items for user {telegram_id}")

    return await service.get_expiring_items(telegram_id, days)
