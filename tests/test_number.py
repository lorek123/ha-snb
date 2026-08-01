"""Test the number platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from storzandbickel_ble.models import DeviceState, DeviceType

from custom_components.storzandbickel.coordinator import (
    StorzBickelDataUpdateCoordinator,
)
from custom_components.storzandbickel.number import (
    BrightnessNumber,
    CraftyAutoOffNumber,
    CraftyBoostTemperatureNumber,
    CraftyLedBrightnessNumber,
    VentyBoostOffsetNumber,
    VentySuperboostOffsetNumber,
    VolcanoAutoOffNumber,
    VolcanoLedBrightnessNumber,
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

    async def test_set_value_calls_set_boost_temperature(
        self, hass: HomeAssistant, mock_entry
    ):
        state = MagicMock(spec=DeviceState)
        state.boost_temperature = None
        device = MagicMock()
        device.set_boost_temperature = AsyncMock()
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = device
        coordinator.data = {"state": state, "device_type": DeviceType.CRAFTY}
        coordinator.async_request_refresh = AsyncMock()
        n = CraftyBoostTemperatureNumber(coordinator)
        await n.async_set_native_value(47)
        device.set_boost_temperature.assert_called_once_with(47.0)
        coordinator.async_request_refresh.assert_called_once()


class TestCraftyLedBrightnessNumber:
    @pytest.fixture
    def coord(self, hass, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.led_brightness = 75
        c = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        c.data = {"state": state, "device_type": DeviceType.CRAFTY}
        return c

    def test_unique_id(self, coord):
        assert (
            CraftyLedBrightnessNumber(coord)._attr_unique_id
            == "test-entry_led_brightness"
        )

    def test_native_value(self, coord):
        assert CraftyLedBrightnessNumber(coord).native_value == 75

    def test_native_value_none(self, coord):
        coord.data = None
        assert CraftyLedBrightnessNumber(coord).native_value is None

    async def test_set_value(self, hass, mock_entry, coord):
        device = MagicMock()
        device.set_led_brightness = AsyncMock()
        coord.device = device
        coord.async_request_refresh = AsyncMock()
        n = CraftyLedBrightnessNumber(coord)
        await n.async_set_native_value(50)
        device.set_led_brightness.assert_called_once_with(50)
        coord.async_request_refresh.assert_called_once()


class TestCraftyAutoOffNumber:
    @pytest.fixture
    def coord(self, hass, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.auto_off_time = 300
        c = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        c.data = {"state": state, "device_type": DeviceType.CRAFTY}
        return c

    def test_unique_id(self, coord):
        assert CraftyAutoOffNumber(coord)._attr_unique_id == "test-entry_auto_off_time"

    def test_native_value(self, coord):
        assert CraftyAutoOffNumber(coord).native_value == 300

    def test_native_value_none(self, coord):
        coord.data = None
        assert CraftyAutoOffNumber(coord).native_value is None

    async def test_set_value(self, hass, mock_entry, coord):
        device = MagicMock()
        device.set_auto_off_time = AsyncMock()
        coord.device = device
        coord.async_request_refresh = AsyncMock()
        n = CraftyAutoOffNumber(coord)
        await n.async_set_native_value(120)
        device.set_auto_off_time.assert_called_once_with(120)
        coord.async_request_refresh.assert_called_once()


class TestVolcanoLedBrightnessNumber:
    @pytest.fixture
    def coord(self, hass, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.led_brightness = 6
        c = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        c.data = {"state": state, "device_type": DeviceType.VOLCANO}
        return c

    def test_unique_id(self, coord):
        assert (
            VolcanoLedBrightnessNumber(coord)._attr_unique_id
            == "test-entry_led_brightness"
        )

    def test_native_value(self, coord):
        assert VolcanoLedBrightnessNumber(coord).native_value == 6

    def test_native_value_none(self, coord):
        coord.data = None
        assert VolcanoLedBrightnessNumber(coord).native_value is None

    async def test_set_value(self, coord):
        device = MagicMock()
        device.set_led_brightness = AsyncMock()
        coord.device = device
        coord.async_request_refresh = AsyncMock()
        await VolcanoLedBrightnessNumber(coord).async_set_native_value(8)
        device.set_led_brightness.assert_called_once_with(8)
        coord.async_request_refresh.assert_called_once()


class TestVolcanoAutoOffNumber:
    @pytest.fixture
    def coord(self, hass, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.auto_off_time = 1800
        c = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        c.data = {"state": state, "device_type": DeviceType.VOLCANO}
        return c

    def test_native_value(self, coord):
        assert VolcanoAutoOffNumber(coord).native_value == 1800

    def test_native_value_none(self, coord):
        coord.data = None
        assert VolcanoAutoOffNumber(coord).native_value is None

    async def test_set_value(self, coord):
        device = MagicMock()
        device.set_auto_off_time = AsyncMock()
        coord.device = device
        coord.async_request_refresh = AsyncMock()
        await VolcanoAutoOffNumber(coord).async_set_native_value(600)
        device.set_auto_off_time.assert_called_once_with(600)
        coord.async_request_refresh.assert_called_once()


class TestVentyBoostOffsetNumber:
    @pytest.fixture
    def coord(self, hass, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.boost_offset = 15
        c = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        c.data = {"state": state, "device_type": DeviceType.VENTY}
        return c

    def test_unique_id(self, coord):
        assert (
            VentyBoostOffsetNumber(coord)._attr_unique_id == "test-entry_boost_offset"
        )

    def test_native_value(self, coord):
        assert VentyBoostOffsetNumber(coord).native_value == 15

    def test_native_value_none(self, coord):
        coord.data = None
        assert VentyBoostOffsetNumber(coord).native_value is None

    async def test_set_value(self, coord):
        device = MagicMock()
        device.set_boost_offset = AsyncMock()
        coord.device = device
        coord.async_request_refresh = AsyncMock()
        await VentyBoostOffsetNumber(coord).async_set_native_value(20)
        device.set_boost_offset.assert_called_once_with(20)
        coord.async_request_refresh.assert_called_once()


class TestVentySuperboostOffsetNumber:
    @pytest.fixture
    def coord(self, hass, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.superboost_offset = 30
        c = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        c.data = {"state": state, "device_type": DeviceType.VEAZY}
        return c

    def test_native_value(self, coord):
        assert VentySuperboostOffsetNumber(coord).native_value == 30

    def test_native_value_none(self, coord):
        coord.data = None
        assert VentySuperboostOffsetNumber(coord).native_value is None

    async def test_set_value(self, coord):
        device = MagicMock()
        device.set_superboost_offset = AsyncMock()
        coord.device = device
        coord.async_request_refresh = AsyncMock()
        await VentySuperboostOffsetNumber(coord).async_set_native_value(25)
        device.set_superboost_offset.assert_called_once_with(25)
        coord.async_request_refresh.assert_called_once()
