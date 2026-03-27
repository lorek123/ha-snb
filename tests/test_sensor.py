"""Test the sensor platform."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from storzandbickel_ble.models import DeviceState, DeviceType

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from custom_components.storzandbickel.const import DOMAIN
from custom_components.storzandbickel.coordinator import StorzBickelDataUpdateCoordinator
from custom_components.storzandbickel.sensor import (
    BatteryLevelSensor,
    ConnectionStateSensor,
    CurrentTemperatureSensor,
    SignalStrengthSensor,
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
    state.current_temperature = 180.0
    state.battery_level = 75
    return state


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_entry, mock_device_state):
    """Create a coordinator with mock data."""
    coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
    coordinator.data = {
        "state": mock_device_state,
        "device_type": DeviceType.CRAFTY,
        "name": "Test Device",
        "address": "AA:BB:CC:DD:EE:FF",
    }
    return coordinator


class TestCurrentTemperatureSensor:
    """Test the current temperature sensor."""

    def test_initialization(self, coordinator):
        """Test sensor initialization."""
        sensor = CurrentTemperatureSensor(coordinator)

        assert sensor._attr_unique_id == "test-entry_current_temperature"
        assert sensor._attr_has_entity_name is True
        assert sensor._attr_translation_key == "current_temperature"
        assert sensor._attr_native_unit_of_measurement == UnitOfTemperature.CELSIUS
        assert sensor._attr_state_class == "measurement"
        assert sensor._attr_device_class == "temperature"

    def test_native_value(self, coordinator, mock_device_state):
        """Test native value property."""
        sensor = CurrentTemperatureSensor(coordinator)

        assert sensor.native_value == 180.0

    def test_native_value_none(self, coordinator):
        """Test native value when data is None."""
        coordinator.data = None
        sensor = CurrentTemperatureSensor(coordinator)

        assert sensor.native_value is None

    def test_device_info_includes_mac_connection(self, coordinator):
        """Device info should expose MAC for Device info panel."""
        sensor = CurrentTemperatureSensor(coordinator)
        info = sensor.device_info
        assert info["connections"] == {(CONNECTION_NETWORK_MAC, "AA:BB:CC:DD:EE:FF")}


class TestBatteryLevelSensor:
    """Test the battery level sensor."""

    def test_initialization(self, coordinator):
        """Test sensor initialization."""
        sensor = BatteryLevelSensor(coordinator)

        assert sensor._attr_unique_id == "test-entry_battery"
        assert sensor._attr_has_entity_name is True
        assert sensor._attr_translation_key == "battery"
        assert sensor._attr_native_unit_of_measurement == PERCENTAGE
        assert sensor._attr_state_class == "measurement"
        assert sensor._attr_device_class == "battery"

    def test_native_value(self, coordinator, mock_device_state):
        """Test native value property."""
        sensor = BatteryLevelSensor(coordinator)

        assert sensor.native_value == 75

    def test_native_value_none(self, coordinator):
        """Test native value when data is None."""
        coordinator.data = None
        sensor = BatteryLevelSensor(coordinator)

        assert sensor.native_value is None

    def test_native_value_no_battery_level(self, coordinator, mock_device_state):
        """Test native value when battery_level is not available."""
        del mock_device_state.battery_level
        sensor = BatteryLevelSensor(coordinator)

        assert sensor.native_value is None


class TestConnectionAndSignalSensors:
    """Test diagnostic connection/signal sensors."""

    def test_connection_state_connected(self, coordinator):
        coordinator.device = MagicMock()
        sensor = ConnectionStateSensor(coordinator)
        assert sensor.native_value == "connected"

    def test_connection_state_disconnected(self, coordinator):
        coordinator.device = None
        sensor = ConnectionStateSensor(coordinator)
        assert sensor.native_value == "disconnected"

    def test_signal_strength_value(self, coordinator, mock_device_state):
        mock_device_state.rssi = -66
        sensor = SignalStrengthSensor(coordinator)
        assert sensor.native_value == -66

    def test_signal_strength_none(self, coordinator, mock_device_state):
        del mock_device_state.rssi
        sensor = SignalStrengthSensor(coordinator)
        assert sensor.native_value is None

    def test_device_info_includes_firmware_and_serial(self, coordinator):
        """Firmware/serial should show up when device exposes them."""
        coordinator.device = MagicMock(
            firmware_version="1.2.3",
            ble_firmware_version="2.0.0",
            serial_number="SN123456",
            address="AA:BB:CC:DD:EE:FF",
        )
        sensor = ConnectionStateSensor(coordinator)
        info = sensor.device_info
        assert info["sw_version"] == "1.2.3 (BLE 2.0.0)"
        assert info["serial_number"] == "SN123456"
