#!/usr/bin/env python3
"""
Database initialization script.

Creates tables and populates with initial data:
- Categories
- Brands
- Default products
"""

import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import select

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database.session import init_db, get_session
from api.models.category import Category
from api.models.brand import Brand
from api.models.product import Product, ProductGTIN

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


async def load_categories() -> int:
    """Load categories from JSON file."""
    file_path = DATA_DIR / "categories.json"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        categories = json.load(f)
    
    async with get_session() as session:
        count = 0
        for cat_data in categories:
            # Check if exists
            result = await session.execute(
                select(Category).where(Category.id == cat_data['id'])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                category = Category(
                    id=cat_data['id'],
                    name=cat_data['name'],
                    icon=cat_data.get('icon')
                )
                session.add(category)
                count += 1
                logger.info(f"Added category: {cat_data['name']}")
        
        await session.commit()
    
    logger.info(f"Loaded {count} new categories")
    return count


async def load_brands() -> int:
    """Load brands from JSON file."""
    file_path = DATA_DIR / "brands.json"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        brands = json.load(f)
    
    async with get_session() as session:
        count = 0
        for brand_data in brands:
            # Check if exists
            result = await session.execute(
                select(Brand).where(Brand.id == brand_data['id'])
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                brand = Brand(
                    id=brand_data['id'],
                    name=brand_data['name']
                )
                session.add(brand)
                count += 1
                logger.info(f"Added brand: {brand_data['name']}")
        
        await session.commit()
    
    logger.info(f"Loaded {count} new brands")
    return count


async def load_products() -> int:
    """Load default products from JSON file."""
    file_path = DATA_DIR / "default_products.json"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    async with get_session() as session:
        count = 0
        for prod_data in products:
            # Check if exists
            result = await session.execute(
                select(Product).where(Product.name.ilike(prod_data['name']))
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                product = Product(
                    name=prod_data['name'],
                    category_id=prod_data.get('category_id'),
                    default_shelf_life_days=prod_data.get('default_shelf_life_days')
                )
                session.add(product)
                count += 1
                logger.info(f"Added product: {prod_data['name']}")
        
        await session.commit()
    
    logger.info(f"Loaded {count} new products")
    return count


async def load_test_gtin_products() -> int:
    """Load test products with GTIN codes for scanning."""
    
    test_products = [
        {
            "name": "Молоко 3.2%",
            "category_id": 1,
            "brand_name": "Домик в деревне",
            "gtin": "04607163091577",
            "default_shelf_life_days": 7
        },
        {
            "name": "Кефир 1%",
            "category_id": 1,
            "brand_name": "Простоквашино",
            "gtin": "04600605034156",
            "default_shelf_life_days": 14
        },
        {
            "name": "Сметана 20%",
            "category_id": 1,
            "brand_name": "Тёма",
            "gtin": "04607004891694",
            "default_shelf_life_days": 14
        },
    ]
    
    async with get_session() as session:
        count = 0
        
        # Get brand IDs
        brand_map = {}
        for prod in test_products:
            brand_name = prod["brand_name"]
            if brand_name not in brand_map:
                result = await session.execute(
                    select(Brand).where(Brand.name == brand_name)
                )
                brand = result.scalar_one_or_none()
                if brand:
                    brand_map[brand_name] = brand.id
        
        for prod_data in test_products:
            # Check if product with this name exists
            result = await session.execute(
                select(Product).where(Product.name == prod_data['name'])
            )
            product = result.scalar_one_or_none()
            
            if not product:
                # Create product
                product = Product(
                    name=prod_data['name'],
                    category_id=prod_data['category_id'],
                    brand_id=brand_map.get(prod_data['brand_name']),
                    default_shelf_life_days=prod_data['default_shelf_life_days']
                )
                session.add(product)
                await session.flush()
                logger.info(f"Added test product: {prod_data['name']}")
            
            # Check if GTIN already exists
            result = await session.execute(
                select(ProductGTIN).where(ProductGTIN.gtin == prod_data['gtin'])
            )
            existing_gtin = result.scalar_one_or_none()
            
            if not existing_gtin:
                # Add GTIN
                gtin_record = ProductGTIN(
                    product_id=product.id,
                    gtin=prod_data['gtin']
                )
                session.add(gtin_record)
                count += 1
                logger.info(f"Added GTIN {prod_data['gtin']} for {prod_data['name']}")
        
        await session.commit()
    
    logger.info(f"Loaded {count} new GTIN records")
    return count


async def main():
    """Initialize database with all data."""
    logger.info("Starting database initialization...")
    
    # Create tables
    logger.info("Creating database tables...")
    await init_db()
    logger.info("Database tables created")
    
    # Load seed data
    logger.info("Loading categories...")
    await load_categories()
    
    logger.info("Loading brands...")
    await load_brands()
    
    logger.info("Loading products...")
    await load_products()
    
    logger.info("Loading test GTIN products...")
    await load_test_gtin_products()
    
    logger.info("Database initialization completed!")


if __name__ == "__main__":
    asyncio.run(main())
