"""Test the integration setup."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from storzandbickel_ble.models import DeviceType

from homeassistant.config_entries import ConfigEntries, ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.storzandbickel import async_setup_entry, async_unload_entry
from custom_components.storzandbickel.data import StorzBickelRuntimeData
from custom_components.storzandbickel.const import (
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_NAME,
    CONF_DEVICE_TYPE,
    DOMAIN,
)


@pytest.fixture
def mock_entry(hass: HomeAssistant):
    """Create a mock config entry registered with hass."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Device",
        entry_id="test-entry",
        data={
            CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF",
            CONF_DEVICE_NAME: "Test Device",
            CONF_DEVICE_TYPE: "crafty",
        },
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_device():
    """Create a mock device."""
    device = AsyncMock()
    device.address = "AA:BB:CC:DD:EE:FF"
    device.name = "Test Device"
    device.device_type = DeviceType.CRAFTY
    return device


class TestIntegrationSetup:
    """Test integration setup and teardown."""

    async def test_setup_entry(self, hass: HomeAssistant, mock_entry, mock_device):
        """Test setting up the integration."""
        mock_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
        with (
            patch(
                "custom_components.storzandbickel.StorzBickelDataUpdateCoordinator"
            ) as mock_coordinator_class,
            patch.object(
                ConfigEntries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.storzandbickel.bluetooth.async_scanner_count",
                return_value=1,
            ),
            patch("custom_components.storzandbickel.ir.async_create_issue"),
            patch("custom_components.storzandbickel.ir.async_delete_issue"),
        ):
            mock_coordinator = MagicMock()
            mock_coordinator.entry = mock_entry
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator.device = mock_device
            mock_coordinator.data = {
                "state": MagicMock(),
                "device_type": DeviceType.CRAFTY,
                "name": "Test Device",
                "address": "AA:BB:CC:DD:EE:FF",
            }
            mock_coordinator_class.return_value = mock_coordinator

            result = await async_setup_entry(hass, mock_entry)

            assert result is True
            runtime = mock_entry.runtime_data
            assert isinstance(runtime, StorzBickelRuntimeData)
            assert runtime.coordinator is mock_coordinator
            mock_coordinator.async_config_entry_first_refresh.assert_called_once()

    async def test_unload_entry(self, hass: HomeAssistant, mock_entry, mock_device):
        """Test unloading the integration."""
        mock_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
        with (
            patch(
                "custom_components.storzandbickel.StorzBickelDataUpdateCoordinator"
            ) as mock_coordinator_class,
            patch.object(
                ConfigEntries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.storzandbickel.bluetooth.async_scanner_count",
                return_value=1,
            ),
            patch("custom_components.storzandbickel.ir.async_create_issue"),
            patch("custom_components.storzandbickel.ir.async_delete_issue"),
        ):
            mock_coordinator = MagicMock()
            mock_coordinator.entry = mock_entry
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator.device = mock_device
            mock_coordinator.data = {
                "state": MagicMock(),
                "device_type": DeviceType.CRAFTY,
                "name": "Test Device",
                "address": "AA:BB:CC:DD:EE:FF",
            }
            mock_coordinator_class.return_value = mock_coordinator

            await async_setup_entry(hass, mock_entry)

            with patch.object(
                ConfigEntries,
                "async_unload_platforms",
                new_callable=AsyncMock,
            ) as mock_unload_platforms:
                mock_unload_platforms.return_value = True

                result = await async_unload_entry(hass, mock_entry)

                assert result is True
                mock_unload_platforms.assert_called_once()
                mock_device.disconnect.assert_called_once()

    async def test_unload_entry_failure(self, hass: HomeAssistant, mock_entry):
        """Test unloading when platform unload fails."""
        mock_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
        with (
            patch(
                "custom_components.storzandbickel.StorzBickelDataUpdateCoordinator"
            ) as mock_coordinator_class,
            patch.object(
                ConfigEntries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.storzandbickel.bluetooth.async_scanner_count",
                return_value=1,
            ),
            patch("custom_components.storzandbickel.ir.async_create_issue"),
            patch("custom_components.storzandbickel.ir.async_delete_issue"),
        ):
            mock_coordinator = MagicMock()
            mock_coordinator.entry = mock_entry
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator.device = None
            mock_coordinator.data = {
                "state": MagicMock(),
                "device_type": DeviceType.CRAFTY,
                "name": "Test Device",
                "address": "AA:BB:CC:DD:EE:FF",
            }
            mock_coordinator_class.return_value = mock_coordinator

            await async_setup_entry(hass, mock_entry)

            with patch.object(
                ConfigEntries,
                "async_unload_platforms",
                new_callable=AsyncMock,
            ) as mock_unload_platforms:
                mock_unload_platforms.return_value = False

                result = await async_unload_entry(hass, mock_entry)

                assert result is False

    async def test_setup_creates_issue_when_no_bluetooth(
        self, hass: HomeAssistant, mock_entry, mock_device
    ):
        """Warning issue if no connectable Bluetooth scanner is configured."""
        mock_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
        with (
            patch(
                "custom_components.storzandbickel.StorzBickelDataUpdateCoordinator"
            ) as mock_coordinator_class,
            patch.object(
                ConfigEntries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.storzandbickel.bluetooth.async_scanner_count",
                return_value=0,
            ),
            patch("custom_components.storzandbickel.ir.async_create_issue") as create_issue,
            patch("custom_components.storzandbickel.ir.async_delete_issue"),
        ):
            mock_coordinator = MagicMock()
            mock_coordinator.entry = mock_entry
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator.device = mock_device
            mock_coordinator.data = {"state": MagicMock(), "device_type": mock_device.device_type}
            mock_coordinator_class.return_value = mock_coordinator

            assert await async_setup_entry(hass, mock_entry) is True
            create_issue.assert_called_once()

    async def test_setup_deletes_issue_when_bluetooth_available(
        self, hass: HomeAssistant, mock_entry, mock_device
    ):
        mock_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
        with (
            patch(
                "custom_components.storzandbickel.StorzBickelDataUpdateCoordinator"
            ) as mock_coordinator_class,
            patch.object(
                ConfigEntries,
                "async_forward_entry_setups",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.storzandbickel.bluetooth.async_scanner_count",
                return_value=1,
            ),
            patch("custom_components.storzandbickel.ir.async_create_issue"),
            patch("custom_components.storzandbickel.ir.async_delete_issue") as delete_issue,
        ):
            mock_coordinator = MagicMock()
            mock_coordinator.entry = mock_entry
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator.device = mock_device
            mock_coordinator.data = {"state": MagicMock(), "device_type": mock_device.device_type}
            mock_coordinator_class.return_value = mock_coordinator

            assert await async_setup_entry(hass, mock_entry) is True
            delete_issue.assert_called_once()
