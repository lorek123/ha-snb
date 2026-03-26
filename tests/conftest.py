"""Pytest configuration and fixtures."""
from __future__ import annotations

import shutil
import sys
import time
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from storzandbickel_ble.models import DeviceState, DeviceType

# Mock aiousbwatcher before Home Assistant imports it
if "aiousbwatcher" not in sys.modules:
    mock_aiousbwatcher = MagicMock()
    mock_aiousbwatcher.AIOUSBWatcher = MagicMock
    mock_aiousbwatcher.InotifyNotAvailableError = Exception
    sys.modules["aiousbwatcher"] = mock_aiousbwatcher

# Minimal PySerial package layout before homeassistant.components.usb imports
# `from serial.tools.list_ports_common import ListPortInfo`.
if "serial" not in sys.modules:
    serial_mod = types.ModuleType("serial")
    tools_mod = types.ModuleType("serial.tools")
    list_ports_mod = types.ModuleType("serial.tools.list_ports")
    list_ports_common_mod = types.ModuleType("serial.tools.list_ports_common")

    class ListPortInfo:
        """Stub for homeassistant.components.usb imports."""

    def _comports() -> list:
        return []

    list_ports_mod.comports = _comports
    list_ports_common_mod.ListPortInfo = ListPortInfo

    tools_mod.list_ports = list_ports_mod
    tools_mod.list_ports_common = list_ports_common_mod
    serial_mod.tools = tools_mod

    sys.modules["serial"] = serial_mod
    sys.modules["serial.tools"] = tools_mod
    sys.modules["serial.tools.list_ports"] = list_ports_mod
    sys.modules["serial.tools.list_ports_common"] = list_ports_common_mod

# Home Assistant test fixtures (provides `hass`, etc. for HA >= 2024)
pytest_plugins = "pytest_homeassistant_custom_component"

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from homeassistant.core import HomeAssistant
from home_assistant_bluetooth import SOURCE_LOCAL, BluetoothServiceInfoBleak


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir: str) -> str:
    """Writable config dir that includes this repo's custom component."""
    dest = Path(hass_tmp_config_dir) / "custom_components" / "storzandbickel"
    src = Path(__file__).resolve().parent.parent / "custom_components" / "storzandbickel"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    return hass_tmp_config_dir


@pytest.fixture(autouse=True)
async def enable_storzandbickel_custom_integrations(
    hass: HomeAssistant,
    enable_custom_integrations,
) -> None:
    """Allow Home Assistant to load custom integrations from the test config directory."""


@pytest.fixture
def mock_device_state():
    """Create a mock device state."""
    state = MagicMock(spec=DeviceState)
    state.current_temperature = 180.0
    state.target_temperature = 185.0
    state.heater_on = True
    state.battery_level = 75
    state.pump_on = False
    return state


@pytest.fixture
def mock_device(mock_device_state):
    """Create a mock StorzBickelDevice."""
    device = AsyncMock()
    device.address = "AA:BB:CC:DD:EE:FF"
    device.name = "Test Device"
    device.device_type = DeviceType.CRAFTY
    device.state = mock_device_state

    device.set_target_temperature = AsyncMock()
    device.turn_heater_on = AsyncMock()
    device.turn_heater_off = AsyncMock()
    device.disconnect = AsyncMock()
    device.update_state = AsyncMock()

    return device


@pytest.fixture
def mock_device_info():
    """Create a mock device info."""
    device_info = MagicMock()
    device_info.address = "AA:BB:CC:DD:EE:FF"
    device_info.name = "Test Device"
    device_info.device_type = DeviceType.CRAFTY
    return device_info


@pytest.fixture
def mock_bluetooth_scanner():
    """Mock bluetooth scanner."""
    with patch(
        "homeassistant.components.bluetooth.async_scanner_count",
        return_value=1,
    ):
        yield


@pytest.fixture
def mock_bluetooth_service_info():
    """Bluetooth discovery payload matching homeassistant.components.bluetooth."""
    device = BLEDevice("AA:BB:CC:DD:EE:FF", "Test Device", {})
    advertisement = AdvertisementData(
        local_name="Test Device",
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=-50,
        platform_data=(),
    )
    return BluetoothServiceInfoBleak.from_device_and_advertisement_data(
        device, advertisement, SOURCE_LOCAL, time.monotonic(), True
    )
