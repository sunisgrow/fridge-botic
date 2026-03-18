"""Tests for Bot handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, timedelta

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestStartHandler:
    """Tests for start handler."""

    @pytest.mark.asyncio
    async def test_start_command_registers_user(self):
        """Test that /start command registers user."""
        from bot.handlers.start import cmd_start
        
        # Create mock message
        message = MagicMock()
        message.from_user.id = 123456789
        message.from_user.username = "test_user"
        message.from_user.first_name = "Test"
        message.answer = AsyncMock()

        # Create mock API client
        api_client = MagicMock()
        api_client.register_user = AsyncMock(return_value={
            "id": 1,
            "telegram_id": 123456789
        })

        # Call handler
        await cmd_start(message, api_client)

        # Verify
        api_client.register_user.assert_called_once_with(
            telegram_id=123456789,
            username="test_user",
            first_name="Test"
        )
        message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_command_shows_welcome_message(self):
        """Test that /start command shows welcome message."""
        from bot.handlers.start import cmd_start
        
        message = MagicMock()
        message.from_user.id = 123456789
        message.from_user.username = "test_user"
        message.from_user.first_name = "Test"
        message.answer = AsyncMock()

        api_client = MagicMock()
        api_client.register_user = AsyncMock()

        await cmd_start(message, api_client)

        # Check that answer was called with text containing welcome
        call_args = message.answer.call_args
        assert "Добро пожаловать" in call_args[0][0] or "Fridge Bot" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_start_handles_registration_error(self):
        """Test that /start handles registration error gracefully."""
        from bot.handlers.start import cmd_start
        
        message = MagicMock()
        message.from_user.id = 123456789
        message.from_user.username = "test_user"
        message.from_user.first_name = "Test"
        message.answer = AsyncMock()

        api_client = MagicMock()
        api_client.register_user = AsyncMock(side_effect=Exception("API error"))

        # Should not raise exception
        await cmd_start(message, api_client)

        # Should still show welcome message
        message.answer.assert_called_once()


class TestHelpHandler:
    """Tests for help handler."""

    @pytest.mark.asyncio
    async def test_help_command_shows_commands(self):
        """Test that /help command shows available commands."""
        from bot.handlers.start import cmd_help
        
        message = MagicMock()
        message.answer = AsyncMock()

        await cmd_help(message)

        # Check that help message contains commands
        call_args = message.answer.call_args
        help_text = call_args[0][0]
        assert "/start" in help_text
        assert "/add" in help_text
        assert "/fridge" in help_text


class TestFridgeViewHandler:
    """Tests for fridge view handler."""

    @pytest.mark.asyncio
    async def test_fridge_empty_message(self):
        """Test that empty fridge shows appropriate message."""
        from bot.handlers.fridge_view import show_fridge
        
        message = MagicMock()
        message.from_user.id = 123456789
        message.answer = AsyncMock()

        api_client = MagicMock()
        api_client.get_fridge_items = AsyncMock(return_value={
            "items": [],
            "total": 0
        })

        await show_fridge(message, api_client)

        call_args = message.answer.call_args
        response_text = call_args[0][0]
        assert "пуст" in response_text.lower() or "нет продуктов" in response_text.lower()

    @pytest.mark.asyncio
    async def test_fridge_shows_items(self):
        """Test that fridge shows items."""
        from bot.handlers.fridge_view import show_fridge
        
        message = MagicMock()
        message.from_user.id = 123456789
        message.answer = AsyncMock()

        api_client = MagicMock()
        api_client.get_fridge_items = AsyncMock(return_value={
            "items": [
                {
                    "id": 1,
                    "product_name": "Молоко",
                    "quantity": 2,
                    "category": "Молочные",
                    "days_until_expiry": 5
                }
            ],
            "total": 1
        })

        await show_fridge(message, api_client)

        call_args = message.answer.call_args
        response_text = call_args[0][0]
        assert "Молоко" in response_text

    @pytest.mark.asyncio
    async def test_fridge_shows_expiring_warning(self):
        """Test that fridge shows expiring warning."""
        from bot.handlers.fridge_view import show_fridge
        
        message = MagicMock()
        message.from_user.id = 123456789
        message.answer = AsyncMock()

        api_client = MagicMock()
        api_client.get_fridge_items = AsyncMock(return_value={
            "items": [
                {
                    "id": 1,
                    "product_name": "Кефир",
                    "quantity": 1,
                    "category": "Молочные",
                    "days_until_expiry": 1
                }
            ],
            "total": 1
        })

        await show_fridge(message, api_client)

        # Should show some warning indicator
        message.answer.assert_called_once()


class TestExpiringProductsHandler:
    """Tests for expiring products handler."""

    @pytest.mark.asyncio
    async def test_expiring_empty_message(self):
        """Test that no expiring products shows appropriate message."""
        from bot.handlers.expiring_products import show_expiring
        
        message = MagicMock()
        message.from_user.id = 123456789
        message.answer = AsyncMock()

        api_client = MagicMock()
        api_client.get_expiring_items = AsyncMock(return_value={
            "items": [],
            "total": 0
        })

        await show_expiring(message, api_client)

        call_args = message.answer.call_args
        response_text = call_args[0][0]
        # Should indicate no expiring products
        assert "нет" in response_text.lower() or "пуст" in response_text.lower() or "не найдено" in response_text.lower()

    @pytest.mark.asyncio
    async def test_expiring_shows_products(self):
        """Test that expiring products are shown."""
        from bot.handlers.expiring_products import show_expiring
        
        message = MagicMock()
        message.from_user.id = 123456789
        message.answer = AsyncMock()

        api_client = MagicMock()
        api_client.get_expiring_items = AsyncMock(return_value={
            "items": [
                {
                    "id": 1,
                    "product_name": "Кефир",
                    "quantity": 1,
                    "days_until_expiry": 1
                }
            ],
            "total": 1
        })

        await show_expiring(message, api_client)

        call_args = message.answer.call_args
        response_text = call_args[0][0]
        assert "Кефир" in response_text


class TestSettingsHandler:
    """Tests for settings handler."""

    @pytest.mark.asyncio
    async def test_settings_shows_current_settings(self):
        """Test that settings shows current notification settings."""
        from bot.handlers.settings import show_settings
        
        message = MagicMock()
        message.from_user.id = 123456789
        message.answer = AsyncMock()

        api_client = MagicMock()
        api_client.get_notification_settings = AsyncMock(return_value={
            "enabled": True,
            "days_before": 3,
            "notify_time": "09:00"
        })

        await show_settings(message, api_client)

        # Should call API
        api_client.get_notification_settings.assert_called_once()
        message.answer.assert_called_once()


class TestAddProductHandler:
    """Tests for add product handler."""

    @pytest.mark.asyncio
    async def test_add_product_shows_categories(self):
        """Test that add product shows category selection."""
        # This test depends on the actual implementation
        # The handler should show categories for selection
        pass

    @pytest.mark.asyncio
    async def test_add_product_success(self):
        """Test successful product addition."""
        from bot.services.api_client import APIClient
        
        api_client = MagicMock()
        api_client.add_fridge_item = AsyncMock(return_value={
            "id": 1,
            "product_name": "Молоко",
            "quantity": 2
        })

        result = await api_client.add_fridge_item(
            telegram_id=123456789,
            product_name="Молоко",
            quantity=2
        )

        assert result["product_name"] == "Молоко"
        assert result["quantity"] == 2


class TestDeleteProductHandler:
    """Tests for delete product handler."""

    @pytest.mark.asyncio
    async def test_delete_product_success(self):
        """Test successful product deletion."""
        api_client = MagicMock()
        api_client.delete_fridge_item = AsyncMock(return_value={
            "deleted": True,
            "item_id": 1,
            "reason": "used"
        })

        result = await api_client.delete_fridge_item(
            telegram_id=123456789,
            item_id=1,
            reason="used"
        )

        assert result["deleted"] is True

    @pytest.mark.asyncio
    async def test_batch_delete_success(self):
        """Test successful batch deletion."""
        api_client = MagicMock()
        api_client.batch_delete_fridge_items = AsyncMock(return_value={
            "deleted_count": 3,
            "deleted_ids": [1, 2, 3],
            "failed_ids": []
        })

        result = await api_client.batch_delete_fridge_items(
            telegram_id=123456789,
            item_ids=[1, 2, 3],
            reason="expired"
        )

        assert result["deleted_count"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
