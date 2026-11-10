"""Tests for binary_sensor platform."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from storzandbickel_ble.models import DeviceState, DeviceType

from custom_components.storzandbickel.binary_sensor import (
    CraftyBoostActiveBinarySensor,
    CraftySuperboostActiveBinarySensor,
    ReadyBinarySensor,
    VentyChargingBinarySensor,
)
from custom_components.storzandbickel.coordinator import (
    StorzBickelDataUpdateCoordinator,
)


@pytest.fixture
def mock_entry():
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry"
    entry.title = "Test Crafty"
    return entry


@pytest.fixture
def venty_coordinator(hass: HomeAssistant, mock_entry):
    state = MagicMock(spec=DeviceState)
    state.charger_connected = True
    state.setpoint_reached = False
    coord = StorzBickelDataUpdateCoordinator(hass, mock_entry)
    coord.data = {"state": state, "device_type": DeviceType.VENTY}
    return coord


class TestVentyChargingBinarySensor:
    def test_unique_id(self, venty_coordinator):
        assert (
            VentyChargingBinarySensor(venty_coordinator)._attr_unique_id
            == "test-entry_charging"
        )

    def test_reflects_charger_connected(self, venty_coordinator):
        assert VentyChargingBinarySensor(venty_coordinator).is_on is True
        venty_coordinator.data["state"].charger_connected = False
        assert VentyChargingBinarySensor(venty_coordinator).is_on is False

    def test_none_when_field_missing(self, venty_coordinator):
        venty_coordinator.data["state"].charger_connected = None
        assert VentyChargingBinarySensor(venty_coordinator).is_on is None

    def test_none_when_no_data(self, venty_coordinator):
        venty_coordinator.data = None
        assert VentyChargingBinarySensor(venty_coordinator).is_on is None


class TestReadyBinarySensor:
    def test_unique_id(self, venty_coordinator):
        assert (
            ReadyBinarySensor(venty_coordinator)._attr_unique_id == "test-entry_ready"
        )

    def test_reflects_setpoint_reached(self, venty_coordinator):
        assert ReadyBinarySensor(venty_coordinator).is_on is False
        venty_coordinator.data["state"].setpoint_reached = True
        assert ReadyBinarySensor(venty_coordinator).is_on is True

    def test_none_when_no_data(self, venty_coordinator):
        venty_coordinator.data = None
        assert ReadyBinarySensor(venty_coordinator).is_on is None

    def test_crafty_setpoint_reached(self, hass: HomeAssistant, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.setpoint_reached = True
        coord = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coord.data = {"state": state, "device_type": DeviceType.CRAFTY}
        assert ReadyBinarySensor(coord).is_on is True


class TestReadyTemperatureFallback:
    @pytest.fixture
    def coord(self, hass: HomeAssistant, mock_entry):
        state = MagicMock()
        state.setpoint_reached = False
        state.heater_on = True
        state.current_temperature = 179.5
        state.target_temperature = 180.0
        c = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        c.data = {"state": state, "device_type": DeviceType.CRAFTY}
        return c

    def test_on_when_within_tolerance(self, coord):
        assert ReadyBinarySensor(coord).is_on is True

    def test_off_while_heating_up(self, coord):
        coord.data["state"].current_temperature = 150.0
        assert ReadyBinarySensor(coord).is_on is False

    def test_off_when_heater_off(self, coord):
        coord.data["state"].heater_on = False
        assert ReadyBinarySensor(coord).is_on is False

    def test_off_when_temperature_unknown(self, coord):
        coord.data["state"].current_temperature = None
        assert ReadyBinarySensor(coord).is_on is False


class TestCraftyBoostBinarySensors:
    @pytest.fixture
    def coord(self, hass: HomeAssistant, mock_entry):
        state = MagicMock()
        state.boost_mode = False
        state.superboost_mode = True
        c = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        c.data = {"state": state, "device_type": DeviceType.CRAFTY}
        return c

    def test_unique_ids(self, coord):
        assert (
            CraftyBoostActiveBinarySensor(coord)._attr_unique_id
            == "test-entry_boost_mode"
        )
        assert (
            CraftySuperboostActiveBinarySensor(coord)._attr_unique_id
            == "test-entry_superboost_mode"
        )

    def test_states(self, coord):
        assert CraftyBoostActiveBinarySensor(coord).is_on is False
        assert CraftySuperboostActiveBinarySensor(coord).is_on is True

    def test_none_when_no_data(self, coord):
        coord.data = None
        assert CraftyBoostActiveBinarySensor(coord).is_on is None
