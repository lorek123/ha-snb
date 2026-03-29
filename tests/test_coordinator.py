"""Test the coordinator."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from storzandbickel_ble import StorzBickelClient
from storzandbickel_ble.exceptions import ConnectionError as SBleConnectionError
from storzandbickel_ble.models import DeviceType
from storzandbickel_ble.protocol import CRAFTY_CHAR_BATTERY, VOLCANO_CHAR_CURRENT_TEMP

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.storzandbickel.const import (
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_NAME,
    CONF_DEVICE_TYPE,
    DOMAIN,
)
from custom_components.storzandbickel.coordinator import StorzBickelDataUpdateCoordinator


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry"
    entry.data = {
        CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF",
        CONF_DEVICE_NAME: "Test Device",
        CONF_DEVICE_TYPE: "crafty",
    }
    entry.title = "Test Device"
    return entry


@pytest.fixture
def mock_device_info():
    """Create a mock device info."""
    device_info = MagicMock()
    device_info.address = "AA:BB:CC:DD:EE:FF"
    device_info.name = "Test Device"
    device_info.device_type = DeviceType.CRAFTY
    return device_info


class TestStorzBickelDataUpdateCoordinator:
    """Test the coordinator."""

    async def test_initialization(self, hass: HomeAssistant, mock_entry):
        """Test coordinator initialization."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        assert coordinator.entry == mock_entry
        assert coordinator.device is None
        assert coordinator._client is None

    async def test_connect_success(
        self, hass: HomeAssistant, mock_entry, mock_device_info, mock_device
    ):
        """Test successful device connection."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock
            ) as mock_connect:
                mock_scan.return_value = [mock_device_info]
                mock_connect.return_value = mock_device

                await coordinator._async_connect()

                assert coordinator.device == mock_device
                mock_scan.assert_called_once()
                mock_connect.assert_called_once_with(mock_device_info)

    async def test_connect_device_not_found(
        self, hass: HomeAssistant, mock_entry
    ):
        """Test connection when device is not found."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = []

            with pytest.raises(UpdateFailed, match="Device.*not found"):
                await coordinator._async_connect()

            assert coordinator.device is None

    async def test_update_data_success(
        self, hass: HomeAssistant, mock_entry, mock_device_info, mock_device
    ):
        """Test successful data update."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock
            ) as mock_connect:
                mock_scan.return_value = [mock_device_info]
                mock_connect.return_value = mock_device

                mock_device._read_characteristic = AsyncMock(return_value=bytearray([80]))

                data = await coordinator._async_update_data()

                assert data["state"] == mock_device.state
                assert data["device_type"] == mock_device.device_type
                assert data["name"] == mock_device.name
                assert data["address"] == mock_device.address
                mock_device.update_state.assert_called_once()
                mock_device._read_characteristic.assert_awaited_once_with(
                    CRAFTY_CHAR_BATTERY
                )

    async def test_update_data_no_device(
        self, hass: HomeAssistant, mock_entry
    ):
        """Test data update when device is not connected."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = None

        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = []

            with pytest.raises(UpdateFailed, match="not found"):
                await coordinator._async_update_data()

    async def test_update_data_error(
        self, hass: HomeAssistant, mock_entry, mock_device_info, mock_device
    ):
        """Test data update when device raises an error."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock
            ) as mock_connect:
                mock_scan.return_value = [mock_device_info]
                mock_connect.return_value = mock_device
                mock_device.update_state.side_effect = Exception("Connection error")

                with pytest.raises(UpdateFailed, match="Error communicating"):
                    await coordinator._async_update_data()

                # Device should be reset on error
                assert coordinator.device is None

    async def test_live_ble_verify_failure_resets_device(
        self, hass: HomeAssistant, mock_entry, mock_device_info, mock_device
    ):
        """Strict post-update GATT read must fail the poll when the link is dead (Crafty)."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock
            ) as mock_connect:
                mock_scan.return_value = [mock_device_info]
                mock_connect.return_value = mock_device
                mock_device._read_characteristic = AsyncMock(
                    side_effect=SBleConnectionError("not connected")
                )

                with pytest.raises(UpdateFailed, match="Error communicating"):
                    await coordinator._async_update_data()

                assert coordinator.device is None
                mock_device._read_characteristic.assert_awaited_once_with(
                    CRAFTY_CHAR_BATTERY
                )

    async def test_live_ble_verify_volcano_uses_current_temp(
        self, hass: HomeAssistant, mock_entry, mock_device_info, mock_device
    ):
        """Volcano uses a strict read on current temperature after update_state."""
        mock_device.device_type = DeviceType.VOLCANO
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock
            ) as mock_connect:
                mock_scan.return_value = [mock_device_info]
                mock_connect.return_value = mock_device
                mock_device._read_characteristic = AsyncMock(return_value=bytearray([1, 2]))

                await coordinator._async_update_data()

                mock_device._read_characteristic.assert_awaited_once_with(
                    VOLCANO_CHAR_CURRENT_TEMP
                )

    async def test_live_ble_verify_skipped_for_venty(
        self, hass: HomeAssistant, mock_entry, mock_device_info, mock_device
    ):
        """Venty update_state already surfaces errors; no extra verify read."""
        mock_device.device_type = DeviceType.VENTY
        mock_device._read_characteristic = AsyncMock()
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock
            ) as mock_connect:
                mock_scan.return_value = [mock_device_info]
                mock_connect.return_value = mock_device

                await coordinator._async_update_data()

                assert mock_device._read_characteristic.await_count == 0

    async def test_shutdown(
        self, hass: HomeAssistant, mock_entry, mock_device_info, mock_device
    ):
        """Test coordinator shutdown."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock
            ) as mock_connect:
                mock_scan.return_value = [mock_device_info]
                mock_connect.return_value = mock_device

                await coordinator._async_connect()
                await coordinator.async_shutdown()

                mock_device.disconnect.assert_called_once()

    async def test_shutdown_no_device(self, hass: HomeAssistant, mock_entry):
        """Test coordinator shutdown when no device is connected."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = None

        # Should not raise an error
        await coordinator.async_shutdown()

    async def test_shutdown_disconnect_error(
        self, hass: HomeAssistant, mock_entry, mock_device_info, mock_device
    ):
        """Disconnect errors during shutdown are logged, not raised."""
        mock_device.disconnect = AsyncMock(side_effect=RuntimeError("fail"))
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock
            ) as mock_connect:
                mock_scan.return_value = [mock_device_info]
                mock_connect.return_value = mock_device

                await coordinator._async_connect()
                await coordinator.async_shutdown()

        mock_device.disconnect.assert_called_once()

    async def test_case_insensitive_address_matching(
        self, hass: HomeAssistant, mock_entry, mock_device_info, mock_device
    ):
        """Test that MAC address matching is case-insensitive."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        mock_entry.data[CONF_DEVICE_ADDRESS] = "aa:bb:cc:dd:ee:ff"
        mock_device_info.address = "AA:BB:CC:DD:EE:FF"

        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock
            ) as mock_connect:
                mock_scan.return_value = [mock_device_info]
                mock_connect.return_value = mock_device

                await coordinator._async_connect()

                assert coordinator.device == mock_device

    async def test_async_disconnect(self, hass: HomeAssistant, mock_entry, mock_device):
        """Disconnect helper clears active device."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = mock_device
        await coordinator.async_disconnect()
        mock_device.disconnect.assert_called_once()
        assert coordinator.device is None

    async def test_async_connect_noop_when_connected(
        self, hass: HomeAssistant, mock_entry, mock_device
    ):
        """Connect helper is a no-op when already connected."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = mock_device
        with patch.object(coordinator, "_async_connect", new_callable=AsyncMock) as connect:
            await coordinator.async_connect()
            connect.assert_not_called()

    async def test_async_reconnect(self, hass: HomeAssistant, mock_entry):
        """Reconnect helper disconnects, connects and refreshes."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.async_disconnect = AsyncMock()
        coordinator.async_connect = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()
        await coordinator.async_reconnect()
        coordinator.async_disconnect.assert_called_once()
        coordinator.async_connect.assert_called_once()
        coordinator.async_request_refresh.assert_called_once()
