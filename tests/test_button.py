"""Test the button platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from storzandbickel_ble.models import DeviceType

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.storzandbickel.button import BoostModeButton
from custom_components.storzandbickel.coordinator import StorzBickelDataUpdateCoordinator


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry"
    entry.title = "Test Device"
    return entry


@pytest.fixture
def mock_device():
    """Create a mock device."""
    device = AsyncMock()
    device.activate_boost_mode = AsyncMock()
    return device


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_entry, mock_device):
    """Create a coordinator with mock device."""
    coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
    coordinator.device = mock_device
    coordinator.data = {
        "state": MagicMock(),
        "device_type": DeviceType.CRAFTY,
        "name": "Test Device",
        "address": "AA:BB:CC:DD:EE:FF",
    }
    return coordinator


class TestBoostModeButton:
    """Test the boost mode button."""

    def test_initialization(self, coordinator):
        """Test button initialization."""
        button = BoostModeButton(coordinator)

        assert button._attr_unique_id == "test-entry_boost"
        assert button._attr_has_entity_name is True
        assert button._attr_translation_key == "boost_mode"

    async def test_press(self, coordinator, mock_device):
        """Test button press."""
        button = BoostModeButton(coordinator)

        await button.async_press()

        mock_device.activate_boost_mode.assert_called_once()

    async def test_press_no_device(self, coordinator):
        """Test button press when device is None."""
        coordinator.device = None
        button = BoostModeButton(coordinator)

        # Should not raise an error
        await button.async_press()

    async def test_press_no_method(self, coordinator):
        """Test button press when device doesn't have the method."""
        coordinator.device = MagicMock()
        del coordinator.device.activate_boost_mode
        button = BoostModeButton(coordinator)

        # Should not raise an error
        await button.async_press()


class TestConnectionButtons:
    """Test reconnect/refresh buttons."""

    async def test_refresh_button(self, coordinator):
        """Refresh button requests refresh."""
        from custom_components.storzandbickel.button import RefreshButton

        coordinator.async_request_refresh = AsyncMock()
        button = RefreshButton(coordinator)
        await button.async_press()
        coordinator.async_request_refresh.assert_called_once()

    async def test_reconnect_button(self, coordinator):
        """Reconnect button triggers reconnect flow."""
        from custom_components.storzandbickel.button import ReconnectButton

        coordinator.async_reconnect = AsyncMock()
        button = ReconnectButton(coordinator)
        await button.async_press()
        coordinator.async_reconnect.assert_called_once()
