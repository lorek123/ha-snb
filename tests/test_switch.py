"""Test the switch platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from storzandbickel_ble.models import DeviceState, DeviceType

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.storzandbickel.coordinator import StorzBickelDataUpdateCoordinator
from custom_components.storzandbickel.switch import (
    AirPumpSwitch,
    BoostTimeoutDisabledSwitch,
    VibrationSwitch,
)


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry"
    entry.title = "Test Device"
    return entry


@pytest.fixture
def mock_device_state():
    """Create a mock device state."""
    state = MagicMock(spec=DeviceState)
    state.pump_on = False
    return state


@pytest.fixture
def mock_device(mock_device_state):
    """Create a mock device."""
    device = AsyncMock()
    device.state = mock_device_state
    device.turn_pump_on = AsyncMock()
    device.turn_pump_off = AsyncMock()
    return device


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_entry, mock_device):
    """Create a coordinator with mock device."""
    coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
    coordinator.device = mock_device
    coordinator.data = {
        "state": mock_device.state,
        "device_type": DeviceType.VOLCANO,
        "name": "Test Device",
        "address": "AA:BB:CC:DD:EE:FF",
    }
    return coordinator


class TestAirPumpSwitch:
    """Test the air pump switch."""

    def test_initialization(self, coordinator):
        """Test switch initialization."""
        switch = AirPumpSwitch(coordinator)

        assert switch._attr_unique_id == "test-entry_air_pump"
        assert switch._attr_has_entity_name is True
        assert switch._attr_translation_key == "air_pump"

    def test_is_on_false(self, coordinator, mock_device_state):
        """Test is_on when air pump is off."""
        mock_device_state.pump_on = False
        switch = AirPumpSwitch(coordinator)

        assert switch.is_on is False

    def test_is_on_true(self, coordinator, mock_device_state):
        """Test is_on when air pump is on."""
        mock_device_state.pump_on = True
        switch = AirPumpSwitch(coordinator)

        assert switch.is_on is True

    def test_is_on_legacy_air_pump_on(self, coordinator, mock_device_state):
        """Legacy state field air_pump_on when pump_on missing."""
        del mock_device_state.pump_on
        mock_device_state.air_pump_on = True
        switch = AirPumpSwitch(coordinator)

        assert switch.is_on is True

    def test_is_on_none(self, coordinator):
        """Test is_on when data is None."""
        coordinator.data = None
        switch = AirPumpSwitch(coordinator)

        assert switch.is_on is False

    def test_is_on_no_pump(self, coordinator, mock_device_state):
        """Test is_on when pump_on is not available."""
        del mock_device_state.pump_on
        switch = AirPumpSwitch(coordinator)

        assert switch.is_on is False

    async def test_turn_on(self, coordinator, mock_device):
        """Test turning the air pump on."""
        switch = AirPumpSwitch(coordinator)

        await switch.async_turn_on()

        mock_device.turn_pump_on.assert_called_once()

    async def test_turn_off(self, coordinator, mock_device):
        """Test turning the air pump off."""
        switch = AirPumpSwitch(coordinator)

        await switch.async_turn_off()

        mock_device.turn_pump_off.assert_called_once()

    async def test_turn_on_no_device(self, coordinator):
        """Test turning on when device is None."""
        coordinator.device = None
        switch = AirPumpSwitch(coordinator)

        # Should not raise an error
        await switch.async_turn_on()

    async def test_turn_off_no_device(self, coordinator):
        """Test turning off when device is None."""
        coordinator.device = None
        switch = AirPumpSwitch(coordinator)

        # Should not raise an error
        await switch.async_turn_off()

    async def test_turn_on_no_method(self, coordinator):
        """Test turning on when device doesn't have the method."""

        class _DeviceWithoutPumpControls:
            pass

        coordinator.device = _DeviceWithoutPumpControls()
        switch = AirPumpSwitch(coordinator)

        # Should not raise an error
        await switch.async_turn_on()


class TestVibrationSwitch:
    """Test vibration switch."""

    @pytest.fixture
    def venty_coordinator(self, hass: HomeAssistant, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.vibration_enabled = True
        device = AsyncMock()
        device.state = state
        device.set_vibration = AsyncMock()
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = device
        coordinator.data = {
            "state": state,
            "device_type": DeviceType.VENTY,
            "name": "Test Device",
            "address": "AA:BB:CC:DD:EE:FF",
        }
        return coordinator

    def test_is_on(self, venty_coordinator):
        sw = VibrationSwitch(venty_coordinator)
        assert sw.is_on is True

    async def test_turn_on_off(self, venty_coordinator):
        sw = VibrationSwitch(venty_coordinator)
        await sw.async_turn_off()
        venty_coordinator.device.set_vibration.assert_called_with(False)
        await sw.async_turn_on()
        venty_coordinator.device.set_vibration.assert_called_with(True)


class TestBoostTimeoutDisabledSwitch:
    """Test boost timeout disabled switch."""

    @pytest.fixture
    def venty_coordinator(self, hass: HomeAssistant, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.boost_timeout_disabled = False
        device = AsyncMock()
        device.state = state
        device.set_boost_timeout_disabled = AsyncMock()
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = device
        coordinator.data = {
            "state": state,
            "device_type": DeviceType.VENTY,
            "name": "Test Device",
            "address": "AA:BB:CC:DD:EE:FF",
        }
        return coordinator

    def test_is_on(self, venty_coordinator):
        sw = BoostTimeoutDisabledSwitch(venty_coordinator)
        assert sw.is_on is False

    async def test_turn_on_off(self, venty_coordinator):
        sw = BoostTimeoutDisabledSwitch(venty_coordinator)
        await sw.async_turn_on()
        venty_coordinator.device.set_boost_timeout_disabled.assert_called_with(True)
        await sw.async_turn_off()
        venty_coordinator.device.set_boost_timeout_disabled.assert_called_with(False)
