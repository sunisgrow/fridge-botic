"""API router for product catalog operations."""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas.product_schema import (
    ProductResponse,
    ProductListResponse,
    CategoryResponse,
    CategoryListResponse
)
from ..repositories.product_repo import ProductRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["products"])


def get_product_repo() -> ProductRepository:
    """Dependency injection for ProductRepository."""
    return ProductRepository()


@router.get("/categories", response_model=CategoryListResponse)
async def get_categories(
    repo: ProductRepository = Depends(get_product_repo)
) -> CategoryListResponse:
    """
    Get all product categories.

    Returns list of categories with icons.
    """
    logger.info("Getting all categories")

    categories = await repo.get_all_categories()

    return CategoryListResponse(
        categories=[
            CategoryResponse(
                id=cat.id,
                name=cat.name,
                icon=cat.icon
            )
            for cat in categories
        ],
        total=len(categories)
    )


@router.get("/search", response_model=ProductListResponse)
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    repo: ProductRepository = Depends(get_product_repo)
) -> ProductListResponse:
    """
    Search products by name.

    Query params:
    - q: Search query (required)
    - limit: Max results (default: 10, range: 1-100)

    Returns list of matching products.
    """
    logger.info(f"Searching products: {q}")

    products = await repo.search_products(q, limit)

    return ProductListResponse(
        products=[
            ProductResponse(
                id=prod.id,
                name=prod.name,
                category_id=prod.category_id,
                category_name=prod.category.name if prod.category else None,
                brand_id=prod.brand_id,
                brand_name=prod.brand.name if prod.brand else None,
                default_shelf_life_days=prod.default_shelf_life_days
            )
            for prod in products
        ],
        total=len(products)
    )


@router.get("/gtin/{gtin}", response_model=ProductResponse)
async def get_product_by_gtin(
    gtin: str,
    repo: ProductRepository = Depends(get_product_repo)
) -> ProductResponse:
    """
    Get product by GTIN code.

    Path params:
    - gtin: GTIN code

    Returns product information or 404 if not found.
    """
    logger.info(f"Getting product by GTIN: {gtin}")

    product = await repo.get_by_gtin(gtin)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductResponse(
        id=product.id,
        name=product.name,
        category_id=product.category_id,
        category_name=product.category.name if product.category else None,
        brand_id=product.brand_id,
        brand_name=product.brand.name if product.brand else None,
        default_shelf_life_days=product.default_shelf_life_days
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    repo: ProductRepository = Depends(get_product_repo)
) -> ProductResponse:
    """
    Get product by ID.

    Path params:
    - product_id: Product ID

    Returns product information or 404 if not found.
    """
    logger.info(f"Getting product {product_id}")

    product = await repo.get_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductResponse(
        id=product.id,
        name=product.name,
        category_id=product.category_id,
        category_name=product.category.name if product.category else None,
        brand_id=product.brand_id,
        brand_name=product.brand.name if product.brand else None,
        default_shelf_life_days=product.default_shelf_life_days
    )
