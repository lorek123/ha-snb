"""Diagnostics tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.storzandbickel.const import (
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_NAME,
    CONF_DEVICE_TYPE,
    DOMAIN,
)
from custom_components.storzandbickel.data import StorzBickelRuntimeData
from custom_components.storzandbickel.diagnostics import async_get_config_entry_diagnostics


@pytest.fixture
def diag_entry(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="My Vaporizer",
        data={
            CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_DEVICE_NAME: "My Vaporizer",
            CONF_DEVICE_TYPE: "venty",
        },
    )
    entry.add_to_hass(hass)
    return entry


async def test_diagnostics_no_runtime(hass: HomeAssistant, diag_entry: MockConfigEntry):
    data = await async_get_config_entry_diagnostics(hass, diag_entry)
    assert data["device_type"] == "venty"
    assert data["device_address_tail"] == "**:**:**:**:DD:EE:FF"
    assert data["coordinator_device_connected"] is False
    assert data["library_version"] is not None


async def test_diagnostics_redact_dash_mac(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Dash",
        data={
            CONF_DEVICE_ADDRESS: "AA-BB-CC-DD-EE-FF",
            CONF_DEVICE_NAME: "Dash",
            CONF_DEVICE_TYPE: "crafty",
        },
    )
    entry.add_to_hass(hass)
    data = await async_get_config_entry_diagnostics(hass, entry)
    assert data["device_address_tail"] == "**-**-**-**-DD-EE-FF"


async def test_diagnostics_redact_fallback(hass: HomeAssistant, diag_entry: MockConfigEntry):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="X",
        data={
            CONF_DEVICE_ADDRESS: "short",
            CONF_DEVICE_NAME: "X",
            CONF_DEVICE_TYPE: "crafty",
        },
    )
    entry.add_to_hass(hass)
    data = await async_get_config_entry_diagnostics(hass, entry)
    assert data["device_address_tail"] == "***"


async def test_diagnostics_unknown_lib_version(hass: HomeAssistant, diag_entry: MockConfigEntry):
    import importlib.metadata

    with patch.object(
        importlib.metadata,
        "version",
        side_effect=importlib.metadata.PackageNotFoundError,
    ):
        data = await async_get_config_entry_diagnostics(hass, diag_entry)
        assert data["library_version"] is None


async def test_diagnostics_with_coordinator(hass: HomeAssistant, diag_entry: MockConfigEntry):
    coord = MagicMock()
    coord.device = object()
    coord.last_update_success = True
    coord.last_exception = None
    diag_entry.runtime_data = StorzBickelRuntimeData(coordinator=coord)

    data = await async_get_config_entry_diagnostics(hass, diag_entry)
    assert data["coordinator_device_connected"] is True
    assert data["last_update_success"] is True


async def test_diagnostics_coordinator_with_exception(
    hass: HomeAssistant, diag_entry: MockConfigEntry
):
    coord = MagicMock()
    coord.device = None
    coord.last_update_success = False
    coord.last_exception = RuntimeError("ble")
    diag_entry.runtime_data = StorzBickelRuntimeData(coordinator=coord)

    data = await async_get_config_entry_diagnostics(hass, diag_entry)
    assert data["last_exception"]
