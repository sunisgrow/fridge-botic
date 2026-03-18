"""Pydantic schemas for shopping list operations."""

from typing import Optional, List

from pydantic import BaseModel, Field


class ShoppingItemBase(BaseModel):
    """Base schema for shopping item."""
    product_name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(default=1, ge=1, le=1000)
    note: Optional[str] = Field(None, max_length=500)


class ShoppingItemCreate(ShoppingItemBase):
    """Schema for creating a shopping item."""
    pass


class ShoppingItemUpdate(BaseModel):
    """Schema for updating a shopping item."""
    quantity: Optional[int] = Field(None, ge=1, le=1000)
    purchased: Optional[bool] = None
    note: Optional[str] = Field(None, max_length=500)


class ShoppingItemResponse(BaseModel):
    """Schema for shopping item response."""
    id: int
    product_name: str
    quantity: int
    purchased: bool = False
    note: Optional[str] = None

    class Config:
        from_attributes = True


class ShoppingListResponse(BaseModel):
    """Schema for shopping list."""
    items: List[ShoppingItemResponse]
    total: int
