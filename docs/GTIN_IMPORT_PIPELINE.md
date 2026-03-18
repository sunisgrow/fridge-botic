# GTIN Import Pipeline

Goal: build product catalog with 1-2 million items.

This enables automatic recognition of most products.

---

## Data Sources

### Primary Sources

1. **Open Food Facts**
   - URL: https://world.openfoodfacts.org/data
   - Size: ~2 million products
   - Format: JSON, CSV
   - Fields: GTIN, name, brand, category, image

2. **Retail Catalogs**
   - Ozon, Wildberries, Яндекс Маркет
   - Size: Varies
   - Access: API, scraping

3. **GS1 Databases**
   - National GS1 organizations
   - Size: Country-specific
   - Access: Limited, requires membership

---

## Import Pipeline

```
┌─────────────────┐
│ Download Dataset │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Fields  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Normalize GTIN  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Deduplicate    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Import to DB    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Build Indexes   │
└─────────────────┘
```

---

## Open Food Facts Import

### Download

```python
import requests
import gzip
import json

OPENFOODFACTS_URL = "https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz"

async def download_off_dataset(output_path: str):
    """Download Open Food Facts dataset."""
    response = requests.get(OPENFOODFACTS_URL, stream=True)
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return output_path
```

### Parse

```python
import gzip
import json

def parse_off_products(filepath: str) -> list[dict]:
    """Parse Open Food Facts JSONL file."""
    products = []
    
    with gzip.open(filepath, 'rt', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                
                # Extract relevant fields
                product = {
                    'gtin': extract_gtin(data),
                    'name': extract_name(data),
                    'brand': extract_brand(data),
                    'category': extract_category(data),
                    'country': data.get('countries', '')
                }
                
                if product['gtin'] and product['name']:
                    products.append(product)
                    
            except json.JSONDecodeError:
                continue
    
    return products

def extract_gtin(data: dict) -> str | None:
    """Extract GTIN from OFF data."""
    # OFF uses 'code' field for GTIN
    code = data.get('code', '')
    
    if code and code.isdigit():
        return normalize_gtin(code)
    return None

def extract_name(data: dict) -> str | None:
    """Extract product name."""
    name = data.get('product_name', '')
    if not name:
        name = data.get('product_name_en', '')
    return name[:255] if name else None

def extract_brand(data: dict) -> str | None:
    """Extract brand name."""
    brands = data.get('brands', '')
    if brands:
        return brands.split(',')[0].strip()[:100]
    return None

def extract_category(data: dict) -> str | None:
    """Extract category."""
    categories = data.get('categories', '')
    if categories:
        return categories.split(',')[0].strip()[:100]
    return None
```

---

## GTIN Normalization

All GTINs must be normalized to 14-digit format.

```python
def normalize_gtin(gtin: str) -> str:
    """
    Normalize GTIN to 14-digit format.
    
    GTIN can be:
    - GTIN-8 (8 digits)
    - GTIN-12 (12 digits, UPC)
    - GTIN-13 (13 digits, EAN)
    - GTIN-14 (14 digits)
    """
    # Remove non-digits
    digits = ''.join(filter(str.isdigit, gtin))
    
    # Pad to 14 digits
    if len(digits) == 8:
        return '000000' + digits
    elif len(digits) == 12:
        return '00' + digits
    elif len(digits) == 13:
        return '0' + digits
    elif len(digits) == 14:
        return digits
    else:
        raise ValueError(f"Invalid GTIN length: {len(digits)}")
```

---

## Deduplication

```python
def deduplicate_products(products: list[dict]) -> list[dict]:
    """Remove duplicate GTINs, keep best record."""
    seen_gtins = {}
    
    for product in products:
        gtin = product['gtin']
        
        if gtin not in seen_gtins:
            seen_gtins[gtin] = product
        else:
            # Keep record with more complete data
            existing = seen_gtins[gtin]
            if is_more_complete(product, existing):
                seen_gtins[gtin] = product
    
    return list(seen_gtins.values())

def is_more_complete(new: dict, existing: dict) -> bool:
    """Check if new record is more complete."""
    new_score = sum(1 for v in new.values() if v)
    existing_score = sum(1 for v in existing.values() if v)
    return new_score > existing_score
```

---

## Database Import

### Batch Insert

```python
from sqlalchemy import text
import asyncio

BATCH_SIZE = 1000

async def import_products_batch(
    session,
    products: list[dict]
) -> int:
    """Import products in batches."""
    imported = 0
    
    # Prepare data
    values = []
    for p in products:
        values.append({
            'name': p['name'],
            'brand': p['brand'],
            'category': p['category'],
            'gtin': p['gtin']
        })
    
    # Bulk insert products
    insert_sql = text("""
        INSERT INTO products (name, brand_id, category_id)
        VALUES (:name, 
            (SELECT id FROM brands WHERE name = :brand),
            (SELECT id FROM categories WHERE name = :category))
        ON CONFLICT DO NOTHING
        RETURNING id
    """)
    
    # Insert GTINs
    gtin_sql = text("""
        INSERT INTO product_gtins (product_id, gtin)
        VALUES (:product_id, :gtin)
        ON CONFLICT (gtin) DO NOTHING
    """)
    
    for i in range(0, len(values), BATCH_SIZE):
        batch = values[i:i+BATCH_SIZE]
        
        for item in batch:
            # Insert product
            result = await session.execute(insert_sql, item)
            product_id = result.scalar()
            
            if product_id:
                # Insert GTIN
                await session.execute(
                    gtin_sql,
                    {'product_id': product_id, 'gtin': item['gtin']}
                )
                imported += 1
        
        await session.commit()
    
    return imported
```

### COPY Command (Fastest)

```python
import csv
import io

async def import_via_copy(session, products: list[dict]):
    """Use PostgreSQL COPY for fastest import."""
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    for p in products:
        writer.writerow([
            p['gtin'],
            p['name'],
            p['brand'] or '',
            p['category'] or ''
        ])
    
    output.seek(0)
    
    # Execute COPY
    await session.execute(text("""
        COPY temp_import (gtin, name, brand, category)
        FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t')
    """))
```

---

## Category Mapping

Map source categories to local categories.

```python
CATEGORY_MAPPING = {
    # Open Food Facts categories
    'dairy': 'Молочные продукты',
    'milk': 'Молочные продукты',
    'cheese': 'Молочные продукты',
    'yogurt': 'Молочные продукты',
    
    'meat': 'Мясо',
    'beef': 'Мясо',
    'pork': 'Мясо',
    'chicken': 'Мясо',
    
    'vegetable': 'Овощи',
    'vegetables': 'Овощи',
    
    'fruit': 'Фрукты',
    'fruits': 'Фрукты',
    
    'beverage': 'Напитки',
    'drink': 'Напитки',
    'juice': 'Напитки',
    
    'frozen': 'Заморозка',
    
    'sauce': 'Соусы',
    
    'bread': 'Хлеб',
    'bakery': 'Хлеб',
    
    'snack': 'Снеки',
}

def map_category(source_category: str) -> str:
    """Map source category to local category."""
    if not source_category:
        return 'Другое'
    
    category_lower = source_category.lower()
    
    for key, mapped in CATEGORY_MAPPING.items():
        if key in category_lower:
            return mapped
    
    return 'Другое'
```

---

## Import Worker

```python
import asyncio
from datetime import datetime

async def import_worker():
    """Background worker for GTIN imports."""
    while True:
        try:
            # Download latest dataset
            log.info("Downloading Open Food Facts dataset...")
            filepath = await download_off_dataset('/tmp/off.jsonl.gz')
            
            # Parse products
            log.info("Parsing products...")
            products = parse_off_products(filepath)
            
            # Normalize and deduplicate
            log.info("Normalizing GTINs...")
            for p in products:
                p['gtin'] = normalize_gtin(p['gtin'])
                p['category'] = map_category(p['category'])
            
            log.info("Deduplicating...")
            products = deduplicate_products(products)
            
            # Import to database
            log.info(f"Importing {len(products)} products...")
            async with get_session() as session:
                imported = await import_products_batch(session, products)
            
            log.info(f"Import complete: {imported} products")
            
            # Update last import time
            await update_import_timestamp()
            
        except Exception as e:
            log.error(f"Import failed: {e}")
        
        # Wait before next import (weekly)
        await asyncio.sleep(7 * 24 * 60 * 60)
```

---

## Incremental Updates

```python
async def import_incremental(since_date: datetime):
    """Import only new/updated products."""
    # Download incremental data
    url = f"{BASE_URL}/diff?since={since_date.isoformat()}"
    
    # Process only changed records
    changes = await fetch_changes(url)
    
    for change in changes:
        if change['action'] == 'create':
            await insert_product(change['product'])
        elif change['action'] == 'update':
            await update_product(change['product'])
        elif change['action'] == 'delete':
            await delete_product(change['gtin'])
```

---

## Performance

| Dataset Size | Import Time |
|--------------|-------------|
| 100K products | ~2 minutes |
| 500K products | ~8 minutes |
| 1M products | ~15 minutes |
| 2M products | ~30 minutes |

Lookup after import: **< 10ms** per GTIN query.

---

## Quality Assurance

```python
async def validate_import():
    """Validate imported data."""
    async with get_session() as session:
        # Check GTIN uniqueness
        duplicates = await session.execute(text("""
            SELECT gtin, COUNT(*) 
            FROM product_gtins 
            GROUP BY gtin 
            HAVING COUNT(*) > 1
        """))
        
        # Check orphaned GTINs
        orphans = await session.execute(text("""
            SELECT pg.gtin 
            FROM product_gtins pg
            LEFT JOIN products p ON pg.product_id = p.id
            WHERE p.id IS NULL
        """))
        
        # Check missing names
        missing_names = await session.execute(text("""
            SELECT COUNT(*) 
            FROM products 
            WHERE name IS NULL OR name = ''
        """))
```

---

## User GTIN Learning

```python
async def save_unknown_gtin(gtin: str, product_name: str, user_id: int):
    """Save user-provided GTIN mapping."""
    async with get_session() as session:
        # Create product
        result = await session.execute(
            text("INSERT INTO products (name) VALUES (:name) RETURNING id"),
            {'name': product_name}
        )
        product_id = result.scalar()
        
        # Link GTIN
        await session.execute(
            text("INSERT INTO product_gtins (product_id, gtin) VALUES (:pid, :gtin)"),
            {'pid': product_id, 'gtin': gtin}
        )
        
        # Log source
        await session.execute(
            text("INSERT INTO gtin_sources (gtin, user_id, created_at) VALUES (:gtin, :uid, NOW())"),
            {'gtin': gtin, 'uid': user_id}
        )
```