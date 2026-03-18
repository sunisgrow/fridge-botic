"""API router for recipe recommendations."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..schemas.recipe_schema import RecipeResponse, RecipeListResponse
from ..services.recipe_service import RecipeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recipes", tags=["recipes"])


def get_recipe_service() -> RecipeService:
    """Dependency injection for RecipeService."""
    return RecipeService()


@router.get("/recommend", response_model=RecipeListResponse)
async def get_recipe_recommendations(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    limit: int = Query(5, ge=1, le=20, description="Max results"),
    service: RecipeService = Depends(get_recipe_service)
) -> RecipeListResponse:
    """
    Get recipe recommendations based on fridge contents.

    Query params:
    - telegram_id: User's Telegram ID (required)
    - limit: Max results (default: 5, range: 1-20)

    Returns list of recommended recipes.
    """
    logger.info(f"Getting recipe recommendations for user {telegram_id}")

    recipes = await service.get_recommendations(telegram_id, limit)

    return recipes


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    service: RecipeService = Depends(get_recipe_service)
) -> RecipeResponse:
    """
    Get recipe by ID.

    Path params:
    - recipe_id: Recipe ID

    Returns recipe details.
    """
    logger.info(f"Getting recipe {recipe_id}")

    recipe = await service.get_recipe_by_id(recipe_id)

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return recipe
