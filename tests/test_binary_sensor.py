"""Tests for binary_sensor platform."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from storzandbickel_ble.models import DeviceState, DeviceType

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.storzandbickel.binary_sensor import ChargingBinarySensor
from custom_components.storzandbickel.coordinator import StorzBickelDataUpdateCoordinator


@pytest.fixture
def mock_entry():
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry"
    entry.title = "Test Crafty"
    return entry


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_entry):
    state = MagicMock(spec=DeviceState)
    state.charging = False
    coord = StorzBickelDataUpdateCoordinator(hass, mock_entry)
    coord.data = {"state": state, "device_type": DeviceType.CRAFTY}
    return coord


class TestChargingBinarySensor:
    def test_unique_id(self, coordinator):
        sensor = ChargingBinarySensor(coordinator)
        assert sensor._attr_unique_id == "test-entry_charging"

    def test_is_off_when_not_charging(self, coordinator):
        coordinator.data["state"].charging = False
        sensor = ChargingBinarySensor(coordinator)
        assert sensor.is_on is False

    def test_is_on_when_charging(self, coordinator):
        coordinator.data["state"].charging = True
        sensor = ChargingBinarySensor(coordinator)
        assert sensor.is_on is True

    def test_none_when_no_data(self, coordinator):
        coordinator.data = None
        sensor = ChargingBinarySensor(coordinator)
        assert sensor.is_on is None
