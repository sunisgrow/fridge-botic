"""Tests for API endpoints."""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    """Create a registered user and return telegram_id."""
    telegram_id = 100000001
    client.post(
        "/api/v1/users/register",
        json={
            "telegram_id": telegram_id,
            "username": "test_user_fixture",
            "first_name": "Test"
        }
    )
    return telegram_id


# =============================================================================
# Health & Root Endpoints
# =============================================================================

class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "fridge-bot-api"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "health" in data


# =============================================================================
# Categories Endpoints
# =============================================================================

class TestCategories:
    """Tests for categories endpoints."""

    def test_get_categories(self, client):
        """Test getting categories list."""
        response = client.get("/api/v1/products/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "total" in data
        assert isinstance(data["categories"], list)

    def test_categories_have_required_fields(self, client):
        """Test that categories have id, name, icon fields."""
        response = client.get("/api/v1/products/categories")
        assert response.status_code == 200
        data = response.json()
        
        if data["total"] > 0:
            category = data["categories"][0]
            assert "id" in category
            assert "name" in category


# =============================================================================
# User Endpoints
# =============================================================================

class TestUserRegistration:
    """Tests for user registration."""

    def test_register_user(self, client):
        """Test user registration."""
        response = client.post(
            "/api/v1/users/register",
            json={
                "telegram_id": 123456789,
                "username": "test_user",
                "first_name": "Test"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["telegram_id"] == 123456789
        assert data["username"] == "test_user"

    def test_register_user_minimal(self, client):
        """Test user registration with minimal data."""
        response = client.post(
            "/api/v1/users/register",
            json={"telegram_id": 123456790}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["telegram_id"] == 123456790

    def test_register_existing_user_returns_same_user(self, client):
        """Test that registering existing user returns same user."""
        telegram_id = 123456791
        
        # First registration
        response1 = client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id, "first_name": "First"}
        )
        assert response1.status_code == 201
        
        # Second registration with same telegram_id
        response2 = client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id, "first_name": "Second"}
        )
        assert response2.status_code == 201
        assert response2.json()["telegram_id"] == telegram_id

    def test_get_user(self, client):
        """Test getting user by telegram ID."""
        # First register user
        client.post(
            "/api/v1/users/register",
            json={
                "telegram_id": 987654321,
                "username": "test_user2",
                "first_name": "Test2"
            }
        )

        # Then get user
        response = client.get("/api/v1/users/987654321")
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == 987654321

    def test_get_nonexistent_user(self, client):
        """Test getting non-existent user returns 404."""
        response = client.get("/api/v1/users/999999999")
        assert response.status_code == 404


# =============================================================================
# Fridge Endpoints
# =============================================================================

class TestFridgeOperations:
    """Tests for fridge operations."""

    def test_get_fridge_items_empty(self, client):
        """Test getting fridge items for new user."""
        response = client.get(
            "/api/v1/fridge/items",
            params={"telegram_id": 111111111}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_add_fridge_item(self, client):
        """Test adding item to fridge."""
        # Register user first
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": 222222222}
        )

        # Add item
        response = client.post(
            "/api/v1/fridge/items",
            params={"telegram_id": 222222222},
            json={
                "product_name": "Молоко",
                "quantity": 2
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["product_name"] == "Молоко"
        assert data["quantity"] == 2

    def test_add_fridge_item_with_expiration(self, client):
        """Test adding item with expiration date."""
        telegram_id = 222222223
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )

        expiration_date = (date.today() + timedelta(days=7)).isoformat()
        response = client.post(
            "/api/v1/fridge/items",
            params={"telegram_id": telegram_id},
            json={
                "product_name": "Йогурт",
                "quantity": 1,
                "expiration_date": expiration_date
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert "expiration_date" in data

    def test_add_fridge_item_nonexistent_user(self, client):
        """Test adding item for non-existent user."""
        response = client.post(
            "/api/v1/fridge/items",
            params={"telegram_id": 888888888},
            json={
                "product_name": "Молоко",
                "quantity": 1
            }
        )
        assert response.status_code == 404

    def test_get_fridge_items_with_items(self, client):
        """Test getting fridge items after adding items."""
        telegram_id = 222222224
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )
        
        # Add item
        client.post(
            "/api/v1/fridge/items",
            params={"telegram_id": telegram_id},
            json={"product_name": "Сыр", "quantity": 1}
        )

        # Get items
        response = client.get(
            "/api/v1/fridge/items",
            params={"telegram_id": telegram_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_update_fridge_item_quantity(self, client):
        """Test updating fridge item quantity."""
        telegram_id = 222222225
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )
        
        # Add item
        add_response = client.post(
            "/api/v1/fridge/items",
            params={"telegram_id": telegram_id},
            json={"product_name": "Масло", "quantity": 1}
        )
        item_id = add_response.json()["id"]

        # Update item
        response = client.patch(
            f"/api/v1/fridge/items/{item_id}",
            params={"telegram_id": telegram_id},
            json={"quantity": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 5

    def test_update_fridge_item_expiration(self, client):
        """Test updating fridge item expiration date."""
        telegram_id = 222222226
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )
        
        # Add item
        add_response = client.post(
            "/api/v1/fridge/items",
            params={"telegram_id": telegram_id},
            json={"product_name": "Сметана", "quantity": 1}
        )
        item_id = add_response.json()["id"]

        # Update expiration
        new_expiration = (date.today() + timedelta(days=14)).isoformat()
        response = client.patch(
            f"/api/v1/fridge/items/{item_id}",
            params={"telegram_id": telegram_id},
            json={"expiration_date": new_expiration}
        )
        assert response.status_code == 200

    def test_update_nonexistent_item(self, client):
        """Test updating non-existent item returns 404."""
        telegram_id = 222222227
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )

        response = client.patch(
            "/api/v1/fridge/items/99999",
            params={"telegram_id": telegram_id},
            json={"quantity": 5}
        )
        assert response.status_code == 404

    def test_delete_fridge_item(self, client):
        """Test deleting fridge item."""
        telegram_id = 222222228
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )

        # Add item
        add_response = client.post(
            "/api/v1/fridge/items",
            params={"telegram_id": telegram_id},
            json={"product_name": "Творог", "quantity": 1}
        )
        item_id = add_response.json()["id"]

        # Delete item
        response = client.delete(
            f"/api/v1/fridge/items/{item_id}",
            params={"telegram_id": telegram_id, "reason": "used"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        assert data["reason"] == "used"

    def test_delete_fridge_item_with_reason_expired(self, client):
        """Test deleting item with expired reason."""
        telegram_id = 222222229
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )
        
        add_response = client.post(
            "/api/v1/fridge/items",
            params={"telegram_id": telegram_id},
            json={"product_name": "Кефир", "quantity": 1}
        )
        item_id = add_response.json()["id"]

        response = client.delete(
            f"/api/v1/fridge/items/{item_id}",
            params={"telegram_id": telegram_id, "reason": "expired"}
        )
        assert response.status_code == 200
        assert response.json()["reason"] == "expired"

    def test_delete_nonexistent_item(self, client):
        """Test deleting non-existent item returns 404."""
        telegram_id = 222222230
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )

        response = client.delete(
            "/api/v1/fridge/items/99999",
            params={"telegram_id": telegram_id}
        )
        assert response.status_code == 404

    def test_batch_delete_fridge_items(self, client):
        """Test batch deleting fridge items."""
        telegram_id = 222222231
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )
        
        # Add multiple items
        item_ids = []
        for i in range(3):
            response = client.post(
                "/api/v1/fridge/items",
                params={"telegram_id": telegram_id},
                json={"product_name": f"Продукт {i}", "quantity": 1}
            )
            item_ids.append(response.json()["id"])

        # Batch delete
        response = client.post(
            "/api/v1/fridge/items/batch-delete",
            params={"telegram_id": telegram_id, "reason": "used"},
            json=item_ids
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 3
        assert len(data["deleted_ids"]) == 3

    def test_get_expiring_items(self, client):
        """Test getting expiring items."""
        telegram_id = 222222232
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )
        
        # Add item expiring soon
        expiration_date = (date.today() + timedelta(days=2)).isoformat()
        client.post(
            "/api/v1/fridge/items",
            params={"telegram_id": telegram_id},
            json={
                "product_name": "Молоко скоропортящееся",
                "quantity": 1,
                "expiration_date": expiration_date
            }
        )

        # Get expiring items
        response = client.get(
            "/api/v1/fridge/expiring",
            params={"telegram_id": telegram_id, "days": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


# =============================================================================
# Products Endpoints
# =============================================================================

class TestProducts:
    """Tests for products endpoints."""

    def test_search_products(self, client):
        """Test searching products."""
        response = client.get(
            "/api/v1/products/search",
            params={"q": "молоко"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "total" in data

    def test_search_products_with_limit(self, client):
        """Test searching products with limit."""
        response = client.get(
            "/api/v1/products/search",
            params={"q": "молоко", "limit": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] <= 5

    def test_search_products_empty_query(self, client):
        """Test searching with empty query returns error."""
        response = client.get(
            "/api/v1/products/search",
            params={"q": ""}
        )
        assert response.status_code == 422  # Validation error

    def test_get_product_by_gtin_not_found(self, client):
        """Test getting product by non-existent GTIN."""
        response = client.get("/api/v1/products/gtin/00000000000000")
        assert response.status_code == 404


# =============================================================================
# Notification Endpoints
# =============================================================================

class TestNotifications:
    """Tests for notification endpoints."""

    def test_get_notification_settings(self, client):
        """Test getting notification settings."""
        telegram_id = 333333331
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )

        response = client.get(
            "/api/v1/notifications/settings",
            params={"telegram_id": telegram_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data

    def test_update_notification_settings_enable(self, client):
        """Test enabling notifications."""
        telegram_id = 333333332
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )

        response = client.post(
            "/api/v1/notifications/settings",
            params={"telegram_id": telegram_id},
            json={"enabled": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True

    def test_update_notification_settings_days_before(self, client):
        """Test updating days before notification."""
        telegram_id = 333333333
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )

        response = client.post(
            "/api/v1/notifications/settings",
            params={"telegram_id": telegram_id},
            json={"days_before": 5}
        )
        assert response.status_code == 200

    def test_update_notification_settings_time(self, client):
        """Test updating notification time."""
        telegram_id = 333333334
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )

        response = client.post(
            "/api/v1/notifications/settings",
            params={"telegram_id": telegram_id},
            json={"notify_time": "10:00"}
        )
        assert response.status_code == 200

    def test_get_expiring_notifications(self, client):
        """Test getting expiring items for notification."""
        telegram_id = 333333335
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )

        response = client.get(
            "/api/v1/notifications/expiring",
            params={"telegram_id": telegram_id}
        )
        assert response.status_code == 200


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_user_workflow(self, client):
        """Test complete user workflow: register, add, update, delete."""
        telegram_id = 444444441

        # 1. Register user
        register_response = client.post(
            "/api/v1/users/register",
            json={
                "telegram_id": telegram_id,
                "username": "integration_user",
                "first_name": "Integration"
            }
        )
        assert register_response.status_code == 201

        # 2. Add product
        add_response = client.post(
            "/api/v1/fridge/items",
            params={"telegram_id": telegram_id},
            json={
                "product_name": "Тестовый продукт",
                "quantity": 3,
                "expiration_date": (date.today() + timedelta(days=5)).isoformat()
            }
        )
        assert add_response.status_code == 201
        item_id = add_response.json()["id"]

        # 3. Get fridge items
        get_response = client.get(
            "/api/v1/fridge/items",
            params={"telegram_id": telegram_id}
        )
        assert get_response.status_code == 200
        assert get_response.json()["total"] >= 1

        # 4. Update item
        update_response = client.patch(
            f"/api/v1/fridge/items/{item_id}",
            params={"telegram_id": telegram_id},
            json={"quantity": 1}
        )
        assert update_response.status_code == 200

        # 5. Delete item
        delete_response = client.delete(
            f"/api/v1/fridge/items/{item_id}",
            params={"telegram_id": telegram_id, "reason": "used"}
        )
        assert delete_response.status_code == 200

    def test_expiring_workflow(self, client):
        """Test workflow with expiring products."""
        telegram_id = 444444442
        client.post(
            "/api/v1/users/register",
            json={"telegram_id": telegram_id}
        )

        # Add expiring product
        expiration_date = (date.today() + timedelta(days=1)).isoformat()
        client.post(
            "/api/v1/fridge/items",
            params={"telegram_id": telegram_id},
            json={
                "product_name": "Скоропортящийся продукт",
                "quantity": 1,
                "expiration_date": expiration_date
            }
        )

        # Check expiring
        response = client.get(
            "/api/v1/fridge/expiring",
            params={"telegram_id": telegram_id, "days": 3}
        )
        assert response.status_code == 200
        assert response.json()["total"] >= 1


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_json(self, client):
        """Test sending invalid JSON returns error."""
        response = client.post(
            "/api/v1/users/register",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_field(self, client):
        """Test missing required field returns validation error."""
        response = client.post(
            "/api/v1/users/register",
            json={}
        )
        assert response.status_code == 422

    def test_invalid_telegram_id_type(self, client):
        """Test invalid telegram_id type returns validation error."""
        response = client.get(
            "/api/v1/users/invalid"
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
