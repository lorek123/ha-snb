"""Test the button platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from storzandbickel_ble.models import DeviceType

from custom_components.storzandbickel.button import FindDeviceButton
from custom_components.storzandbickel.coordinator import (
    StorzBickelDataUpdateCoordinator,
)


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


class TestFindDeviceButton:
    @pytest.fixture
    def coord(self, hass, mock_entry):
        from storzandbickel_ble.models import DeviceType

        c = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        c.data = {"state": MagicMock(), "device_type": DeviceType.CRAFTY}
        c.device = MagicMock()
        c.device.find_device = AsyncMock()
        return c

    def test_unique_id(self, coord):
        assert FindDeviceButton(coord)._attr_unique_id == "test-entry_find_device"

    async def test_press_calls_find_device(self, coord):
        btn = FindDeviceButton(coord)
        await btn.async_press()
        coord.device.find_device.assert_called_once()

    async def test_press_no_device(self, coord):
        coord.device = None
        btn = FindDeviceButton(coord)
        await btn.async_press()  # should not raise
