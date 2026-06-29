"""Tests for binary_sensor platform."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from storzandbickel_ble.models import DeviceState, DeviceType

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.storzandbickel.binary_sensor import (
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
