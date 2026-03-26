"""Test the select platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from storzandbickel_ble.models import DeviceState, DeviceType

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.storzandbickel.coordinator import StorzBickelDataUpdateCoordinator
from custom_components.storzandbickel.select import VolcanoWorkflowPresetSelect


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

