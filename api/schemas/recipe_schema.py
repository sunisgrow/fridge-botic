"""Pydantic schemas for recipe operations."""

from typing import Optional, List

from pydantic import BaseModel, Field


class IngredientResponse(BaseModel):
    """Schema for ingredient response."""
    id: int
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None

    class Config:
        from_attributes = True


class RecipeResponse(BaseModel):
    """Schema for recipe response."""
    id: int
    name: str
    description: Optional[str] = None
    cooking_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    ingredients: List[IngredientResponse] = []
    instructions: Optional[str] = None
    image_url: Optional[str] = None
    match_score: Optional[float] = None

    class Config:
        from_attributes = True


class RecipeListResponse(BaseModel):
    """Schema for list of recipes."""
    recipes: List[RecipeResponse]
    total: int
