"""Tests for Bot API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.services.api_client import APIClient


class TestAPIClient:
    """Tests for APIClient class."""

    @pytest.fixture
    def api_client(self):
        """Create API client instance."""
        client = APIClient(base_url="http://test-api:8000/api/v1")
        yield client
        # Cleanup not needed as we mock the client

    @pytest.mark.asyncio
    async def test_register_user(self, api_client):
        """Test user registration."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "telegram_id": 123456789,
            "username": "test_user"
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(api_client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await api_client.register_user(
                telegram_id=123456789,
                username="test_user",
                first_name="Test"
            )
            
            assert result["telegram_id"] == 123456789
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user(self, api_client):
        """Test getting user."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "telegram_id": 123456789,
            "username": "test_user"
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(api_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await api_client.get_user(123456789)
            
            assert result["telegram_id"] == 123456789

    @pytest.mark.asyncio
    async def test_get_fridge_items(self, api_client):
        """Test getting fridge items."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {"id": 1, "product_name": "Молоко", "quantity": 2}
            ],
            "total": 1
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(api_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await api_client.get_fridge_items(telegram_id=123456789)
            
            assert result["total"] == 1
            assert len(result["items"]) == 1

    @pytest.mark.asyncio
    async def test_add_fridge_item(self, api_client):
        """Test adding fridge item."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "product_name": "Молоко",
            "quantity": 2
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(api_client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await api_client.add_fridge_item(
                telegram_id=123456789,
                product_name="Молоко",
                quantity=2
            )
            
            assert result["product_name"] == "Молоко"
            assert result["quantity"] == 2

    @pytest.mark.asyncio
    async def test_update_fridge_item(self, api_client):
        """Test updating fridge item."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "product_name": "Молоко",
            "quantity": 5
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(api_client.client, 'patch', new_callable=AsyncMock) as mock_patch:
            mock_patch.return_value = mock_response
            
            result = await api_client.update_fridge_item(
                telegram_id=123456789,
                item_id=1,
                quantity=5
            )
            
            assert result["quantity"] == 5

    @pytest.mark.asyncio
    async def test_delete_fridge_item(self, api_client):
        """Test deleting fridge item."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "deleted": True,
            "item_id": 1,
            "reason": "used"
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(api_client.client, 'delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = mock_response
            
            result = await api_client.delete_fridge_item(
                telegram_id=123456789,
                item_id=1,
                reason="used"
            )
            
            assert result["deleted"] is True
            assert result["reason"] == "used"

    @pytest.mark.asyncio
    async def test_batch_delete_fridge_items(self, api_client):
        """Test batch deleting fridge items."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "deleted_count": 3,
            "deleted_ids": [1, 2, 3],
            "failed_ids": []
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(api_client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await api_client.batch_delete_fridge_items(
                telegram_id=123456789,
                item_ids=[1, 2, 3],
                reason="expired"
            )
            
            assert result["deleted_count"] == 3

    @pytest.mark.asyncio
    async def test_get_expiring_items(self, api_client):
        """Test getting expiring items."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {"id": 1, "product_name": "Кефир", "days_until_expiry": 1}
            ],
            "total": 1
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(api_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await api_client.get_expiring_items(
                telegram_id=123456789,
                days=3
            )
            
            assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_get_categories(self, api_client):
        """Test getting categories."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "categories": [
                {"id": 1, "name": "Молочные", "icon": "🥛"}
            ],
            "total": 1
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(api_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await api_client.get_categories()
            
            assert len(result) == 1
            assert result[0]["name"] == "Молочные"

    @pytest.mark.asyncio
    async def test_search_products(self, api_client):
        """Test searching products."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "products": [
                {"id": 1, "name": "Молоко Домик в деревне"}
            ],
            "total": 1
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(api_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await api_client.search_products(query="молоко", limit=10)
            
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_notification_settings(self, api_client):
        """Test getting notification settings."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "enabled": True,
            "days_before": 3,
            "notify_time": "09:00"
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(api_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            result = await api_client.get_notification_settings(telegram_id=123456789)
            
            assert result["enabled"] is True
            assert result["days_before"] == 3

    @pytest.mark.asyncio
    async def test_update_notification_settings(self, api_client):
        """Test updating notification settings."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "enabled": False,
            "days_before": 5,
            "notify_time": "10:00"
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(api_client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await api_client.update_notification_settings(
                telegram_id=123456789,
                enabled=False,
                days_before=5
            )
            
            assert result["enabled"] is False

    @pytest.mark.asyncio
    async def test_close_client(self, api_client):
        """Test closing client."""
        with patch.object(api_client.client, 'aclose', new_callable=AsyncMock) as mock_close:
            await api_client.close()
            mock_close.assert_called_once()


class TestAPIClientErrors:
    """Tests for API client error handling."""

    @pytest.fixture
    def api_client(self):
        """Create API client instance."""
        client = APIClient(base_url="http://test-api:8000/api/v1")
        yield client

    @pytest.mark.asyncio
    async def test_http_error_handling(self, api_client):
        """Test HTTP error handling."""
        with patch.object(api_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPError("Connection error")
            
            with pytest.raises(httpx.HTTPError):
                await api_client.get_user(123456789)

    @pytest.mark.asyncio
    async def test_404_error_handling(self, api_client):
        """Test 404 error handling."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found",
            request=MagicMock(),
            response=MagicMock(status_code=404)
        )

        with patch.object(api_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            with pytest.raises(httpx.HTTPStatusError):
                await api_client.get_user(999999999)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
