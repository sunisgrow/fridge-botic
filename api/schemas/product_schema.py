"""Pydantic schemas for product operations."""

from typing import Optional

from pydantic import BaseModel, Field


class CategoryResponse(BaseModel):
    """Schema for category response."""
    id: int
    name: str
    icon: Optional[str] = None

    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    """Schema for list of categories."""
    categories: list[CategoryResponse]
    total: int


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: int
    name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    brand_id: Optional[int] = None
    brand_name: Optional[str] = None
    default_shelf_life_days: Optional[int] = None

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for list of products."""
    products: list[ProductResponse]
    total: int
