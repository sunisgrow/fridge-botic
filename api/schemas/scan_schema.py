"""Pydantic schemas for scanning operations."""

from typing import Optional

from pydantic import BaseModel, Field


class ScanResponse(BaseModel):
    """Schema for scan response."""
    success: bool
    message: str
    gtin: Optional[str] = None
    
    # Информация о товаре
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    brand_name: Optional[str] = None
    default_shelf_life: Optional[int] = None
    
    # Данные из DataMatrix
    expiration_date: Optional[str] = None
    serial: Optional[str] = None
    batch: Optional[str] = None
    ai93: Optional[str] = None
    raw_data: Optional[str] = None

    class Config:
        from_attributes = True
