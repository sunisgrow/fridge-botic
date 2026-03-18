"""Business logic for scanning operations."""

import logging
from typing import Optional

from ..schemas.scan_schema import ScanResponse

logger = logging.getLogger(__name__)

# Import scanner module
from scanner import scan_datamatrix as scan_datamatrix_lib
from ..repositories.product_repo import ProductRepository


class ScanService:
    """
    Business logic for scanning operations.

    Responsibilities:
    - Process DataMatrix codes
    - Process receipt images
    - Extract product information
    """

    def __init__(self):
        self.product_repo = ProductRepository()

    async def process_datamatrix(
        self,
        image_data: bytes,
        telegram_id: int
    ) -> ScanResponse:
        """
        Process DataMatrix code from image.

        Args:
            image_data: Image binary data
            telegram_id: User's Telegram ID

        Returns:
            Decoded DataMatrix information
        """
        logger.info(f"Processing DataMatrix for user {telegram_id}")

        try:
            # Scan DataMatrix code
            scan_result = scan_datamatrix_lib(image_data)

            if not scan_result.get('success'):
                return ScanResponse(
                    success=False,
                    message=scan_result.get('error', 'Scan failed'),
                    gtin=None
                )

            gtin = scan_result.get('gtin')
            logger.info(f"Scanned GTIN: {gtin}")

            # Lookup product by GTIN
            product = None
            product_name = None
            category_id = None
            category_name = None
            brand_name = None
            default_shelf_life = None

            if gtin:
                product = await self.product_repo.get_by_gtin(gtin)
                if product:
                    product_name = product.name
                    category_id = product.category_id
                    category_name = product.category.name if product.category else None
                    brand_name = product.brand.name if product.brand else None
                    default_shelf_life = product.default_shelf_life_days
                    logger.info(f"Found product: {product_name}")
                else:
                    logger.info(f"Product not found for GTIN: {gtin}")

            if product:
                message = "Товар найден"
            else:
                message = "Товар не найден в базе. Добавьте вручную."

            return ScanResponse(
                success=True,
                message=message,
                gtin=gtin,
                product_id=product.id if product else None,
                product_name=product_name,
                category_id=category_id,
                category_name=category_name,
                brand_name=brand_name,
                default_shelf_life=default_shelf_life,
                expiration_date=scan_result.get('expiration_date'),
                serial=scan_result.get('serial'),
                batch=scan_result.get('batch'),
                ai93=scan_result.get('ai93'),
                raw_data=scan_result.get('raw_data')
            )

        except Exception as e:
            logger.error(f"Error processing DataMatrix: {e}", exc_info=True)
            return ScanResponse(
                success=False,
                message=f"Ошибка при обработке: {str(e)}",
                gtin=None
            )

    async def process_receipt(
        self,
        image_data: bytes,
        telegram_id: int
    ) -> dict:
        """
        Process receipt image and extract products.

        Args:
            image_data: Image binary data
            telegram_id: User's Telegram ID

        Returns:
            Extracted products from receipt
        """
        # TODO: Implement receipt scanning
        # For now, return placeholder response
        logger.info(f"Processing receipt for user {telegram_id}")

        return {
            "success": False,
            "message": "Receipt scanning not implemented yet",
            "products": []
        }

    async def lookup_by_gtin(
        self,
        gtin: str,
        telegram_id: int,
        raw_data: Optional[str] = None
    ) -> ScanResponse:
        """
        Lookup product by GTIN (from WebApp scanner).

        Args:
            gtin: GTIN/EAN code
            telegram_id: User's Telegram ID
            raw_data: Raw barcode data (optional)

        Returns:
            Product information if found
        """
        logger.info(f"Looking up product by GTIN: {gtin} for user {telegram_id}")

        try:
            product = await self.product_repo.get_by_gtin(gtin)

            if product:
                logger.info(f"Found product: {product.name}")
                return ScanResponse(
                    success=True,
                    message="Товар найден",
                    gtin=gtin,
                    product_id=product.id,
                    product_name=product.name,
                    category_id=product.category_id,
                    category_name=product.category.name if product.category else None,
                    brand_name=product.brand.name if product.brand else None,
                    default_shelf_life=product.default_shelf_life_days,
                    raw_data=raw_data
                )
            else:
                logger.info(f"Product not found for GTIN: {gtin}")
                return ScanResponse(
                    success=True,
                    message="Товар не найден в базе. Добавьте вручную.",
                    gtin=gtin,
                    raw_data=raw_data
                )

        except Exception as e:
            logger.error(f"Error looking up product: {e}", exc_info=True)
            return ScanResponse(
                success=False,
                message=f"Ошибка при поиске: {str(e)}",
                gtin=gtin
            )
