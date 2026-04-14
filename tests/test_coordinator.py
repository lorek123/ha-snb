"""Test the coordinator."""
from __future__ import annotations

import time
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

BT_SCANNER = "homeassistant.components.bluetooth.async_ble_device_from_address"


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
def mock_ble_device():
    """Create a mock BLEDevice as returned by HA's bluetooth scanner."""
    ble = MagicMock()
    ble.name = "STORZ&BICKEL"
    ble.address = "AA:BB:CC:DD:EE:FF"
    return ble


class TestStorzBickelDataUpdateCoordinator:
    """Test the coordinator."""

    async def test_initialization(self, hass: HomeAssistant, mock_entry):
        """Test coordinator initialization."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        assert coordinator.entry == mock_entry
        assert coordinator.device is None
        assert coordinator._consecutive_connect_failures == 0
        assert coordinator._next_connect_attempt == 0.0

    async def test_connect_success(
        self, hass: HomeAssistant, mock_entry, mock_ble_device, mock_device
    ):
        """Test successful device connection via HA bluetooth scanner."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch(BT_SCANNER, return_value=mock_ble_device):
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock
            ) as mock_connect:
                mock_connect.return_value = mock_device

                await coordinator._async_connect()

                assert coordinator.device == mock_device
                assert coordinator._consecutive_connect_failures == 0
                mock_connect.assert_called_once()

    async def test_connect_device_not_visible(
        self, hass: HomeAssistant, mock_entry
    ):
        """Test connection when device is not visible to HA bluetooth scanner."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch(BT_SCANNER, return_value=None):
            with pytest.raises(UpdateFailed, match="not in range"):
                await coordinator._async_connect()

        assert coordinator.device is None
        assert coordinator._consecutive_connect_failures == 1

    async def test_connect_schedules_backoff_on_failure(
        self, hass: HomeAssistant, mock_entry, mock_ble_device
    ):
        """Connection failure schedules a backoff window."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch(BT_SCANNER, return_value=mock_ble_device):
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock,
                side_effect=Exception("GATT error"),
            ):
                with pytest.raises(UpdateFailed):
                    await coordinator._async_connect()

        assert coordinator._consecutive_connect_failures == 1
        assert coordinator._next_connect_attempt > time.monotonic()

    async def test_backoff_skips_connection_attempt(
        self, hass: HomeAssistant, mock_entry
    ):
        """Update is skipped without touching the proxy while in backoff window."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator._next_connect_attempt = time.monotonic() + 60.0

        with patch(BT_SCANNER) as mock_scanner:
            with pytest.raises(UpdateFailed, match="backing off"):
                await coordinator._async_update_data()

            mock_scanner.assert_not_called()

    async def test_backoff_resets_on_success(
        self, hass: HomeAssistant, mock_entry, mock_ble_device, mock_device
    ):
        """Successful connection clears the backoff counter."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator._consecutive_connect_failures = 3
        coordinator._next_connect_attempt = time.monotonic() + 120.0

        with patch(BT_SCANNER, return_value=mock_ble_device):
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock,
                return_value=mock_device,
            ):
                coordinator._next_connect_attempt = 0.0  # expire backoff for this call
                await coordinator._async_connect()

        assert coordinator._consecutive_connect_failures == 0
        assert coordinator._next_connect_attempt == 0.0

    async def test_update_data_success(
        self, hass: HomeAssistant, mock_entry, mock_ble_device, mock_device
    ):
        """Test successful data update."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch(BT_SCANNER, return_value=mock_ble_device):
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock,
                return_value=mock_device,
            ):
                mock_device._read_characteristic = AsyncMock(return_value=bytearray([80]))

                data = await coordinator._async_update_data()

                assert data["state"] == mock_device.state
                assert data["device_type"] == mock_device.device_type
                assert data["name"] == mock_device.name
                assert data["address"] == mock_device.address
                mock_device.update_state.assert_called_once()
                mock_device._read_characteristic.assert_awaited_once_with(CRAFTY_CHAR_BATTERY)

    async def test_update_data_device_not_visible(
        self, hass: HomeAssistant, mock_entry
    ):
        """Data update raises UpdateFailed when device is not visible."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch(BT_SCANNER, return_value=None):
            with pytest.raises(UpdateFailed, match="not in range"):
                await coordinator._async_update_data()

    async def test_update_data_error(
        self, hass: HomeAssistant, mock_entry, mock_ble_device, mock_device
    ):
        """Test data update when device raises an error."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch(BT_SCANNER, return_value=mock_ble_device):
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock,
                return_value=mock_device,
            ):
                mock_device.update_state.side_effect = Exception("Connection error")

                with pytest.raises(UpdateFailed, match="Error communicating"):
                    await coordinator._async_update_data()

                assert coordinator.device is None

    async def test_live_ble_verify_failure_resets_device(
        self, hass: HomeAssistant, mock_entry, mock_ble_device, mock_device
    ):
        """Strict post-update GATT read must fail the poll when the link is dead (Crafty)."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch(BT_SCANNER, return_value=mock_ble_device):
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock,
                return_value=mock_device,
            ):
                mock_device._read_characteristic = AsyncMock(
                    side_effect=SBleConnectionError("not connected")
                )

                with pytest.raises(UpdateFailed, match="Error communicating"):
                    await coordinator._async_update_data()

                assert coordinator.device is None
                mock_device._read_characteristic.assert_awaited_once_with(CRAFTY_CHAR_BATTERY)

    async def test_live_ble_verify_volcano_uses_current_temp(
        self, hass: HomeAssistant, mock_entry, mock_ble_device, mock_device
    ):
        """Volcano uses a strict read on current temperature after update_state."""
        mock_device.device_type = DeviceType.VOLCANO
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch(BT_SCANNER, return_value=mock_ble_device):
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock,
                return_value=mock_device,
            ):
                mock_device._read_characteristic = AsyncMock(return_value=bytearray([1, 2]))

                await coordinator._async_update_data()

                mock_device._read_characteristic.assert_awaited_once_with(VOLCANO_CHAR_CURRENT_TEMP)

    async def test_live_ble_verify_skipped_for_venty(
        self, hass: HomeAssistant, mock_entry, mock_ble_device, mock_device
    ):
        """Venty update_state already surfaces errors; no extra verify read."""
        mock_device.device_type = DeviceType.VENTY
        mock_device._read_characteristic = AsyncMock()
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch(BT_SCANNER, return_value=mock_ble_device):
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock,
                return_value=mock_device,
            ):
                await coordinator._async_update_data()

                assert mock_device._read_characteristic.await_count == 0

    async def test_shutdown(
        self, hass: HomeAssistant, mock_entry, mock_ble_device, mock_device
    ):
        """Test coordinator shutdown."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch(BT_SCANNER, return_value=mock_ble_device):
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock,
                return_value=mock_device,
            ):
                await coordinator._async_connect()
                await coordinator.async_shutdown()

                mock_device.disconnect.assert_called_once()

    async def test_shutdown_no_device(self, hass: HomeAssistant, mock_entry):
        """Test coordinator shutdown when no device is connected."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator.device = None

        await coordinator.async_shutdown()

    async def test_shutdown_disconnect_error(
        self, hass: HomeAssistant, mock_entry, mock_ble_device, mock_device
    ):
        """Disconnect errors during shutdown are logged, not raised."""
        mock_device.disconnect = AsyncMock(side_effect=RuntimeError("fail"))
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch(BT_SCANNER, return_value=mock_ble_device):
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock,
                return_value=mock_device,
            ):
                await coordinator._async_connect()
                await coordinator.async_shutdown()

        mock_device.disconnect.assert_called_once()

    async def test_case_insensitive_address_matching(
        self, hass: HomeAssistant, mock_entry, mock_ble_device, mock_device
    ):
        """MAC address is normalised to uppercase before querying HA scanner."""
        mock_entry.data[CONF_DEVICE_ADDRESS] = "aa:bb:cc:dd:ee:ff"
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)

        with patch(BT_SCANNER, return_value=mock_ble_device) as mock_scanner:
            with patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock,
                return_value=mock_device,
            ):
                await coordinator._async_connect()

        # Coordinator must pass the uppercased address to the HA scanner
        mock_scanner.assert_called_once_with(hass, "AA:BB:CC:DD:EE:FF", connectable=True)
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
        """Reconnect helper resets backoff, disconnects, connects and refreshes."""
        coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
        coordinator._consecutive_connect_failures = 5
        coordinator._next_connect_attempt = time.monotonic() + 120.0
        coordinator.async_disconnect = AsyncMock()
        coordinator.async_connect = AsyncMock()
        coordinator.async_request_refresh = AsyncMock()

        await coordinator.async_reconnect()

        assert coordinator._consecutive_connect_failures == 0
        assert coordinator._next_connect_attempt == 0.0
        coordinator.async_disconnect.assert_called_once()
        coordinator.async_connect.assert_called_once()
        coordinator.async_request_refresh.assert_called_once()
