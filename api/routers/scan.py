"""API router for scanning operations."""

import json
import logging
from typing import Optional

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query, Body, File, UploadFile

from ..schemas.scan_schema import ScanResponse
from ..services.scan_service import ScanService
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scan", tags=["scan"])


def get_redis_client():
    """Get Redis client for scan results."""
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_scan_service() -> ScanService:
    """Dependency injection for ScanService."""
    return ScanService()


@router.post("/datamatrix", response_model=ScanResponse)
async def scan_datamatrix(
    file: UploadFile = File(..., description="Image file with DataMatrix code"),
    telegram_id: int = Query(..., description="User's Telegram ID"),
    service: ScanService = Depends(get_scan_service)
) -> ScanResponse:
    """
    Scan DataMatrix code from image.

    Query params:
    - telegram_id: User's Telegram ID (required)

    Request body:
    - file: Image file (required)

    Returns decoded DataMatrix information.
    """
    logger.info(f"Scanning DataMatrix for user {telegram_id}")

    # Read image data
    image_data = await file.read()

    # Process scan
    result = await service.process_datamatrix(image_data, telegram_id)

    return result


@router.post("/receipt")
async def scan_receipt(
    file: UploadFile = File(..., description="Receipt image file"),
    telegram_id: int = Query(..., description="User's Telegram ID"),
    service: ScanService = Depends(get_scan_service)
) -> dict:
    """
    Scan receipt and extract products.

    Query params:
    - telegram_id: User's Telegram ID (required)

    Request body:
    - file: Receipt image file (required)

    Returns extracted products from receipt.
    """
    logger.info(f"Scanning receipt for user {telegram_id}")

    # Read image data
    image_data = await file.read()

    # Process receipt
    result = await service.process_receipt(image_data, telegram_id)

    return result


@router.post("/lookup", response_model=ScanResponse)
async def lookup_product(
    gtin: str = Body(..., description="GTIN/EAN code"),
    raw_data: str = Body(None, description="Raw barcode data"),
    telegram_id: int = Query(..., description="User's Telegram ID"),
    service: ScanService = Depends(get_scan_service)
) -> ScanResponse:
    """
    Lookup product by GTIN (from WebApp scanner).

    Query params:
    - telegram_id: User's Telegram ID (required)

    Request body:
    - gtin: GTIN/EAN code (required)
    - raw_data: Raw barcode data (optional)

    Returns product information if found.
    """
    logger.info(f"Looking up product by GTIN: {gtin} for user {telegram_id}")

    result = await service.lookup_by_gtin(gtin, telegram_id, raw_data)

    return result


@router.post("/webapp")
async def receive_webapp_scan(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    raw: str = Body(None, description="Raw barcode data"),
    gtin: str = Body(None, description="GTIN code"),
    serial: str = Body(None, description="Serial number"),
    scan_format: str = Body(None, description="Scan format")
):
    """
    Receive scan data from Mini App and store in Redis for bot to retrieve.
    
    Query params:
    - telegram_id: User's Telegram ID (required)
    
    Request body:
    - raw: Raw barcode data
    - gtin: GTIN/EAN code
    - serial: Serial number
    - scan_format: Format name
    
    Returns success status.
    """
    import time
    logger.info(f"Received webapp scan for user {telegram_id}: gtin={gtin}")
    
    try:
        redis_client = get_redis_client()
        
        scan_data = {
            "raw": raw or "",
            "gtin": gtin or "",
            "serial": serial or "",
            "format": scan_format or "",
            "timestamp": str(int(time.time()))
        }
        
        # Store in Redis with 5 minute expiration
        key = f"webapp_scan:{telegram_id}"
        await redis_client.set(key, json.dumps(scan_data), ex=300)
        
        await redis_client.close()
        
        logger.info(f"Stored webapp scan result for user {telegram_id}")
        
        return {"success": True, "message": "Scan data received"}
        
    except Exception as e:
        logger.error(f"Error storing webapp scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webapp/result")
async def get_webapp_scan_result(
    telegram_id: int = Query(..., description="User's Telegram ID")
):
    """
    Get scan result from Mini App (consumes the result).
    
    Query params:
    - telegram_id: User's Telegram ID (required)
    
    Returns scan data if available, or null.
    """
    logger.info(f"Getting webapp scan result for user {telegram_id}")
    
    try:
        redis_client = get_redis_client()
        
        key = f"webapp_scan:{telegram_id}"
        data = await redis_client.get(key)
        
        # Delete the key after reading (one-time use)
        if data:
            await redis_client.delete(key)
            await redis_client.close()
            
            scan_data = json.loads(data)
            logger.info(f"Retrieved webapp scan result for user {telegram_id}: {scan_data}")
            return scan_data
        
        await redis_client.close()
        return None
        
    except Exception as e:
        logger.error(f"Error getting webapp scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
