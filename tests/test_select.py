"""Test the select platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from storzandbickel_ble.models import DeviceState, DeviceType, HeaterMode

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.storzandbickel.coordinator import (
    StorzBickelDataUpdateCoordinator,
)
from custom_components.storzandbickel.select import (
    VentyHeaterModeSelect,
    VolcanoWorkflowPresetSelect,
)


@pytest.fixture
def mock_entry():
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry"
    entry.title = "Test Device"
    return entry


class TestVolcanoWorkflowPresetSelect:
    async def test_select_option(self, hass: HomeAssistant, mock_entry):
        state = MagicMock(spec=DeviceState)
        device = AsyncMock()
        device.run_workflow_preset = AsyncMock()
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = device
        coordinator.data = {"state": state, "device_type": DeviceType.VOLCANO}

        sel = VolcanoWorkflowPresetSelect(coordinator)
        await sel.async_select_option("flow1")
        device.run_workflow_preset.assert_called_once_with("flow1")

    async def test_select_invalid_option_noop(self, hass: HomeAssistant, mock_entry):
        state = MagicMock(spec=DeviceState)
        device = AsyncMock()
        device.run_workflow_preset = AsyncMock()
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = device
        coordinator.data = {"state": state, "device_type": DeviceType.VOLCANO}

        sel = VolcanoWorkflowPresetSelect(coordinator)
        await sel.async_select_option("not_a_preset")
        device.run_workflow_preset.assert_not_called()


class TestVentyHeaterModeSelect:
    @pytest.fixture
    def coord(self, hass: HomeAssistant, mock_entry):
        state = MagicMock(spec=DeviceState)
        state.heater_mode = HeaterMode.BOOST
        c = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        c.device = AsyncMock()
        c.device.set_heater_mode = AsyncMock()
        c.data = {"state": state, "device_type": DeviceType.VENTY}
        return c

    def test_current_option(self, coord):
        assert VentyHeaterModeSelect(coord).current_option == "boost"

    def test_current_option_off_is_none(self, coord):
        coord.data["state"].heater_mode = HeaterMode.OFF
        assert VentyHeaterModeSelect(coord).current_option is None

    def test_current_option_no_data(self, coord):
        coord.data = None
        assert VentyHeaterModeSelect(coord).current_option is None

    async def test_select_option(self, coord):
        await VentyHeaterModeSelect(coord).async_select_option("superboost")
        coord.device.set_heater_mode.assert_called_once_with(HeaterMode.SUPERBOOST)

    async def test_select_invalid_noop(self, coord):
        await VentyHeaterModeSelect(coord).async_select_option("nope")
        coord.device.set_heater_mode.assert_not_called()
