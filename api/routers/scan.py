"""API router for scanning operations."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body, File, UploadFile

from ..schemas.scan_schema import ScanResponse
from ..services.scan_service import ScanService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scan", tags=["scan"])


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
