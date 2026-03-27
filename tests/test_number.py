"""Test the number platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from storzandbickel_ble.models import DeviceState, DeviceType

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.storzandbickel.coordinator import StorzBickelDataUpdateCoordinator
from custom_components.storzandbickel.number import (
    BrightnessNumber,
    CraftyBoostTemperatureNumber,
)


@pytest.fixture
def mock_entry():
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry"
    entry.title = "Test Device"
    return entry


class TestBrightnessNumber:
    def test_native_value(self, hass: HomeAssistant, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.brightness = 9
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.data = {"state": state, "device_type": DeviceType.VENTY}
        n = BrightnessNumber(coordinator)
        assert n.native_value == 9

    async def test_set_value(self, hass: HomeAssistant, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.brightness = 5
        device = AsyncMock()
        device.set_brightness = AsyncMock()
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = device
        coordinator.data = {"state": state, "device_type": DeviceType.VENTY}
        n = BrightnessNumber(coordinator)
        await n.async_set_native_value(3)
        device.set_brightness.assert_called_once_with(3)

    async def test_set_value_without_method(self, hass: HomeAssistant, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.brightness = 5
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = object()
        coordinator.data = {"state": state, "device_type": DeviceType.VENTY}
        coordinator.async_request_refresh = AsyncMock()
        n = BrightnessNumber(coordinator)
        await n.async_set_native_value(3)
        coordinator.async_request_refresh.assert_not_called()


class TestCraftyBoostTemperatureNumber:
    def test_native_value(self, hass: HomeAssistant, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.boost_temperature = 20.0
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.data = {"state": state, "device_type": DeviceType.CRAFTY}
        n = CraftyBoostTemperatureNumber(coordinator)
        assert n.native_value == 20.0

    async def test_set_value(self, hass: HomeAssistant, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.boost_temperature = 10.0
        device = AsyncMock()
        device.set_boost_temperature = AsyncMock()
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = device
        coordinator.data = {"state": state, "device_type": DeviceType.CRAFTY}
        n = CraftyBoostTemperatureNumber(coordinator)
        await n.async_set_native_value(42)
        device.set_boost_temperature.assert_called_once_with(42.0)

    async def test_set_value_without_method(self, hass: HomeAssistant, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.boost_temperature = 10.0
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = object()
        coordinator.data = {"state": state, "device_type": DeviceType.CRAFTY}
        coordinator.async_request_refresh = AsyncMock()
        n = CraftyBoostTemperatureNumber(coordinator)
        await n.async_set_native_value(42)
        coordinator.async_request_refresh.assert_not_called()

    def test_native_value_fallback_fields(self, hass: HomeAssistant, mock_entry):
        """Read value from alternate upstream state field names."""
        state = MagicMock(spec=DeviceState)
        state.boost_temperature = None
        state.boost_temp = None
        state.boost_offset = 33
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.data = {"state": state, "device_type": DeviceType.CRAFTY}
        n = CraftyBoostTemperatureNumber(coordinator)
        assert n.native_value == 33.0

    async def test_set_value_with_offset_method(self, hass: HomeAssistant, mock_entry):
        """Use alternate upstream method name when present."""
        state = MagicMock(spec=DeviceState)
        state.boost_temperature = None
        device = MagicMock()
        device.set_boost_offset = AsyncMock()
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = device
        coordinator.data = {"state": state, "device_type": DeviceType.CRAFTY}
        coordinator.async_request_refresh = AsyncMock()
        n = CraftyBoostTemperatureNumber(coordinator)
        await n.async_set_native_value(47)
        device.set_boost_offset.assert_called_once_with(47.0)
        coordinator.async_request_refresh.assert_called_once()

