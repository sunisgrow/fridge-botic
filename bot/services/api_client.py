"""API client for communicating with backend."""

import logging
from typing import Optional, List

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class APIClient:
    """HTTP client for API communication."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.API_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    # ==================== Users ====================

    async def register_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> dict:
        """Register new user."""
        response = await self.client.post(
            f"{self.base_url}/users/register",
            json={
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_user(self, telegram_id: int) -> dict:
        """Get user information."""
        response = await self.client.get(
            f"{self.base_url}/users/{telegram_id}"
        )
        response.raise_for_status()
        return response.json()

    # ==================== Fridge ====================

    async def get_fridge_items(
        self,
        telegram_id: int,
        category_id: Optional[int] = None,
        expiring_days: Optional[int] = None
    ) -> dict:
        """
        Get all items in user's fridge.

        Args:
            telegram_id: User's Telegram ID
            category_id: Optional category filter
            expiring_days: Optional filter for expiring items

        Returns:
            Dict with items list and total count
        """
        params = {"telegram_id": telegram_id}

        if category_id:
            params["category_id"] = category_id
        if expiring_days is not None:
            params["expiring_days"] = expiring_days

        response = await self.client.get(
            f"{self.base_url}/fridge/items",
            params=params
        )
        response.raise_for_status()
        return response.json()

    async def add_fridge_item(
        self,
        telegram_id: int,
        product_name: str,
        category_id: Optional[int] = None,
        brand_name: Optional[str] = None,
        quantity: int = 1,
        expiration_date: Optional[str] = None,
        note: Optional[str] = None
    ) -> dict:
        """
        Add item to fridge.

        Args:
            telegram_id: User's Telegram ID
            product_name: Product name
            category_id: Category ID
            brand_name: Brand name
            quantity: Quantity
            expiration_date: Expiration date (YYYY-MM-DD)
            note: Custom note

        Returns:
            Created fridge item
        """
        data = {
            "product_name": product_name,
            "quantity": quantity
        }

        if category_id:
            data["category_id"] = category_id
        if brand_name:
            data["brand_name"] = brand_name
        if expiration_date:
            data["expiration_date"] = expiration_date
        if note:
            data["note"] = note

        response = await self.client.post(
            f"{self.base_url}/fridge/items",
            params={"telegram_id": telegram_id},
            json=data
        )
        response.raise_for_status()
        return response.json()

    async def update_fridge_item(
        self,
        telegram_id: int,
        item_id: int,
        quantity: Optional[int] = None,
        expiration_date: Optional[str] = None,
        opened: Optional[bool] = None,
        note: Optional[str] = None
    ) -> dict:
        """Update fridge item."""
        data = {}

        if quantity is not None:
            data["quantity"] = quantity
        if expiration_date is not None:
            data["expiration_date"] = expiration_date
        if opened is not None:
            data["opened"] = opened
        if note is not None:
            data["note"] = note

        response = await self.client.patch(
            f"{self.base_url}/fridge/items/{item_id}",
            params={"telegram_id": telegram_id},
            json=data
        )
        response.raise_for_status()
        return response.json()

    async def delete_fridge_item(
        self,
        telegram_id: int,
        item_id: int,
        reason: Optional[str] = None
    ) -> dict:
        """Delete fridge item."""
        params = {"telegram_id": telegram_id}

        if reason:
            params["reason"] = reason

        response = await self.client.delete(
            f"{self.base_url}/fridge/items/{item_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()

    async def batch_delete_fridge_items(
        self,
        telegram_id: int,
        item_ids: List[int],
        reason: Optional[str] = None
    ) -> dict:
        """Batch delete fridge items."""
        params = {"telegram_id": telegram_id}

        if reason:
            params["reason"] = reason

        response = await self.client.post(
            f"{self.base_url}/fridge/items/batch-delete",
            params=params,
            json=item_ids
        )
        response.raise_for_status()
        return response.json()

    async def get_expiring_items(
        self,
        telegram_id: int,
        days: int = 3
    ) -> dict:
        """Get items expiring within specified days."""
        response = await self.client.get(
            f"{self.base_url}/fridge/expiring",
            params={
                "telegram_id": telegram_id,
                "days": days
            }
        )
        response.raise_for_status()
        return response.json()

    # ==================== Products ====================

    async def get_categories(self) -> list[dict]:
        """Get all product categories."""
        response = await self.client.get(
            f"{self.base_url}/products/categories"
        )
        response.raise_for_status()
        data = response.json()
        return data.get("categories", [])

    async def search_products(
        self,
        query: str,
        limit: int = 10
    ) -> list[dict]:
        """Search products by name."""
        response = await self.client.get(
            f"{self.base_url}/products/search",
            params={
                "q": query,
                "limit": limit
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("products", [])

    async def get_webapp_scan_result(self, telegram_id: int) -> Optional[dict]:
        """Get scan result from Mini App (one-time, consumes the result)."""
        response = await self.client.get(
            f"{self.base_url}/scan/webapp/result",
            params={"telegram_id": telegram_id}
        )
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        data = response.json()
        return data
        response.raise_for_status()
        data = response.json()
        return data.get("products", [])

    # ==================== Notifications ====================

    async def get_notification_settings(
        self,
        telegram_id: int
    ) -> dict:
        """Get user's notification settings."""
        response = await self.client.get(
            f"{self.base_url}/notifications/settings",
            params={"telegram_id": telegram_id}
        )
        response.raise_for_status()
        return response.json()

    async def update_notification_settings(
        self,
        telegram_id: int,
        enabled: Optional[bool] = None,
        days_before: Optional[int] = None,
        notify_time: Optional[str] = None
    ) -> dict:
        """Update notification settings."""
        data = {}

        if enabled is not None:
            data["enabled"] = enabled
        if days_before is not None:
            data["days_before"] = days_before
        if notify_time is not None:
            data["notify_time"] = notify_time

        response = await self.client.post(
            f"{self.base_url}/notifications/settings",
            params={"telegram_id": telegram_id},
            json=data
        )
        response.raise_for_status()
        return response.json()

    # ==================== Recipes ====================

    async def get_recipe_recommendations(
        self,
        telegram_id: int,
        limit: int = 5
    ) -> dict:
        """Get recipe recommendations."""
        response = await self.client.get(
            f"{self.base_url}/recipes/recommend",
            params={
                "telegram_id": telegram_id,
                "limit": limit
            }
        )
        response.raise_for_status()
        return response.json()

    # ==================== Shopping ====================

    async def get_shopping_list(
        self,
        telegram_id: int
    ) -> dict:
        """Get shopping list."""
        response = await self.client.get(
            f"{self.base_url}/shopping/list",
            params={"telegram_id": telegram_id}
        )
        response.raise_for_status()
        return response.json()

    async def add_shopping_item(
        self,
        telegram_id: int,
        product_name: str,
        quantity: int = 1,
        note: Optional[str] = None
    ) -> dict:
        """Add item to shopping list."""
        data = {
            "product_name": product_name,
            "quantity": quantity
        }

        if note:
            data["note"] = note

        response = await self.client.post(
            f"{self.base_url}/shopping/items",
            params={"telegram_id": telegram_id},
            json=data
        )
        response.raise_for_status()
        return response.json()

    # ==================== Scan ====================

    async def scan_datamatrix(
        self,
        telegram_id: int,
        file_bytes: bytes,
        filename: str = "photo.jpg"
    ) -> dict:
        """
        Scan DataMatrix code from image.

        Args:
            telegram_id: User's Telegram ID
            file_bytes: Image binary data
            filename: Image filename

        Returns:
            Scan result with product info
        """
        files = {"file": (filename, file_bytes, "image/jpeg")}
        response = await self.client.post(
            f"{self.base_url}/scan/datamatrix",
            params={"telegram_id": telegram_id},
            files=files
        )
        response.raise_for_status()
        return response.json()

    async def lookup_product(
        self,
        telegram_id: int,
        gtin: str,
        raw_data: str = None
    ) -> dict:
        """
        Lookup product by GTIN (from WebApp scanner).

        Args:
            telegram_id: User's Telegram ID
            gtin: GTIN/EAN code
            raw_data: Raw barcode data

        Returns:
            Product info if found
        """
        data = {"gtin": gtin}
        if raw_data:
            data["raw_data"] = raw_data
            
        response = await self.client.post(
            f"{self.base_url}/scan/lookup",
            params={"telegram_id": telegram_id},
            json=data
        )
        response.raise_for_status()
        return response.json()
