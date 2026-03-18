"""Pydantic schemas for fridge operations."""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DeleteReason(str, Enum):
    """Reason for deleting a fridge item."""
    USED = "used"
    EXPIRED = "expired"
    OTHER = "other"


class FridgeItemBase(BaseModel):
    """Base schema for fridge item."""
    product_name: str = Field(..., min_length=1, max_length=255)
    brand_name: Optional[str] = Field(None, max_length=100)
    category_id: Optional[int] = None
    quantity: int = Field(default=1, ge=1, le=1000)
    expiration_date: Optional[date] = None
    zone_id: Optional[int] = None
    opened: bool = False
    note: Optional[str] = Field(None, max_length=500)


class FridgeItemCreate(FridgeItemBase):
    """Schema for creating a fridge item."""
    pass


class FridgeItemUpdate(BaseModel):
    """Schema for updating a fridge item."""
    quantity: Optional[int] = Field(None, ge=1, le=1000)
    expiration_date: Optional[date] = None
    opened: Optional[bool] = None
    note: Optional[str] = Field(None, max_length=500)


class FridgeItemDelete(BaseModel):
    """Schema for deleting a fridge item."""
    reason: Optional[DeleteReason] = None


class FridgeItemResponse(BaseModel):
    """Schema for fridge item response."""
    id: int
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    category_icon: Optional[str] = None
    quantity: int
    expiration_date: Optional[date] = None
    days_until_expiry: Optional[int] = None
    added_at: Optional[str] = None
    opened: bool = False
    note: Optional[str] = None
    zone_name: Optional[str] = None

    class Config:
        from_attributes = True


class FridgeItemListResponse(BaseModel):
    """Schema for list of fridge items."""
    items: list[FridgeItemResponse]
    total: int


class FridgeResponse(BaseModel):
    """Schema for fridge response."""
    id: int
    name: str
    items_count: int = 0
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class FridgeListResponse(BaseModel):
    """Schema for list of fridges."""
    fridges: list[FridgeResponse]


class FridgeCreate(BaseModel):
    """Schema for creating a fridge."""
    name: str = Field(..., min_length=1, max_length=100)
