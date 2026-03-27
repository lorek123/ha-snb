"""Exercise platform async_setup_entry branches for coverage."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from storzandbickel_ble.models import DeviceType

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.storzandbickel import button, climate, number, select, sensor, switch
from custom_components.storzandbickel.const import (
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_NAME,
    CONF_DEVICE_TYPE,
)
from custom_components.storzandbickel.coordinator import StorzBickelDataUpdateCoordinator
from custom_components.storzandbickel.data import StorzBickelRuntimeData


@pytest.fixture
def flow_entry():
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "e1"
    entry.title = "Platform test device"
    entry.data = {
        CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF",
        CONF_DEVICE_NAME: "T",
        CONF_DEVICE_TYPE: "crafty",
    }
    entry.runtime_data = None
    return entry


def _coord(hass: HomeAssistant, entry: MagicMock, device_type: DeviceType):
    coordinator = StorzBickelDataUpdateCoordinator(hass, entry)
    coordinator.data = {"state": MagicMock(), "device_type": device_type}
    entry.runtime_data = StorzBickelRuntimeData(coordinator=coordinator)
    return coordinator


@pytest.mark.parametrize(
    ("device_type", "expected_boost"),
    [
        (DeviceType.VOLCANO, 2),
        (DeviceType.VENTY, 3),
        (DeviceType.VEAZY, 3),
        (DeviceType.CRAFTY, 3),
    ],
)
async def test_button_platform_entities(
    hass: HomeAssistant, flow_entry: MagicMock, device_type: DeviceType, expected_boost: int
):
    _coord(hass, flow_entry, device_type)
    added = MagicMock()
    await button.async_setup_entry(hass, flow_entry, added)
    assert len(added.call_args[0][0]) == expected_boost


async def test_climate_platform_adds_one(hass: HomeAssistant, flow_entry: MagicMock):
    _coord(hass, flow_entry, DeviceType.CRAFTY)
    added = MagicMock()
    await climate.async_setup_entry(hass, flow_entry, added)
    assert len(added.call_args[0][0]) == 1


@pytest.mark.parametrize(
    ("device_type", "expected_numbers"),
    [
        (DeviceType.VOLCANO, 0),
        (DeviceType.VENTY, 1),
        (DeviceType.VEAZY, 1),
        (DeviceType.CRAFTY, 1),
    ],
)
async def test_number_platform(
    hass: HomeAssistant,
    flow_entry: MagicMock,
    device_type: DeviceType,
    expected_numbers: int,
):
    _coord(hass, flow_entry, device_type)
    added = MagicMock()
    await number.async_setup_entry(hass, flow_entry, added)
    assert len(added.call_args[0][0]) == expected_numbers


@pytest.mark.parametrize(
    ("device_type", "expected_select"),
    [
        (DeviceType.VOLCANO, 1),
        (DeviceType.CRAFTY, 0),
    ],
)
async def test_select_platform(
    hass: HomeAssistant,
    flow_entry: MagicMock,
    device_type: DeviceType,
    expected_select: int,
):
    _coord(hass, flow_entry, device_type)
    added = MagicMock()
    await select.async_setup_entry(hass, flow_entry, added)
    assert len(added.call_args[0][0]) == expected_select


@pytest.mark.parametrize(
    ("device_type", "expected_entities"),
    [
        (DeviceType.VOLCANO, 3),
        (DeviceType.VENTY, 4),
        (DeviceType.VEAZY, 4),
        (DeviceType.CRAFTY, 4),
    ],
)
async def test_sensor_platform(
    hass: HomeAssistant,
    flow_entry: MagicMock,
    device_type: DeviceType,
    expected_entities: int,
):
    """Always temp+connection+signal; battery on portable lines."""
    _coord(hass, flow_entry, device_type)
    added = MagicMock()
    await sensor.async_setup_entry(hass, flow_entry, added)
    assert len(added.call_args[0][0]) == expected_entities


@pytest.mark.parametrize(
    ("device_type", "expected_switches"),
    [
        (DeviceType.VOLCANO, 1),
        (DeviceType.VENTY, 2),
        (DeviceType.VEAZY, 2),
        (DeviceType.CRAFTY, 0),
    ],
)
async def test_switch_platform(
    hass: HomeAssistant,
    flow_entry: MagicMock,
    device_type: DeviceType,
    expected_switches: int,
):
    _coord(hass, flow_entry, device_type)
    added = MagicMock()
    await switch.async_setup_entry(hass, flow_entry, added)
    assert len(added.call_args[0][0]) == expected_switches
