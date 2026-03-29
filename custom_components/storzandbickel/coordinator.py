"""Data update coordinator for Storz & Bickel."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from storzandbickel_ble import StorzBickelClient
from storzandbickel_ble.models import DeviceType
from storzandbickel_ble.protocol import CRAFTY_CHAR_BATTERY, VOLCANO_CHAR_CURRENT_TEMP

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_DEVICE_ADDRESS, CONF_DEVICE_NAME, CONF_DEVICE_TYPE, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)

# storzandbickel_ble Crafty/Volcano update_state() swallows most GATT errors, so a failed
# poll can still return without raising and leave stale state — last_update_success stays True.
UPDATE_STATE_TIMEOUT = 90.0
LIVE_BLE_VERIFY_TIMEOUT = 25.0


class StorzBickelDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Storz & Bickel device."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.entry = entry
        self.device: Any = None  # Concrete type from storzandbickel_ble (varies by device)
        self._client: StorzBickelClient | None = None
        self._connect_lock = asyncio.Lock()
        self._connect_error_logged = False

    async def _async_verify_live_ble_link(self) -> None:
        """Perform one strict GATT read so out-of-range / dead links fail the coordinator update.

        Crafty and Volcano update_state() catch errors per-characteristic and only log them,
        so update_state() can return while the device is unreachable. Venty-style devices
        already raise from command timeouts and do not need this.
        """
        device = self.device
        if device is None:
            return
        device_type = device.device_type
        if device_type == DeviceType.CRAFTY:
            char = CRAFTY_CHAR_BATTERY
        elif device_type == DeviceType.VOLCANO:
            char = VOLCANO_CHAR_CURRENT_TEMP
        else:
            return
        await asyncio.wait_for(
            device._read_characteristic(char),
            timeout=LIVE_BLE_VERIFY_TIMEOUT,
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from the device."""
        if self.device is None:
            async with self._connect_lock:
                if self.device is None:
                    await self._async_connect()

        if self.device is None:
            raise UpdateFailed("Device not connected")

        try:
            await asyncio.wait_for(
                self.device.update_state(),
                timeout=UPDATE_STATE_TIMEOUT,
            )
            await self._async_verify_live_ble_link()
            if self._connect_error_logged:
                _LOGGER.info(
                    "Connection restored to device %s",
                    self.device.name or self.entry.data[CONF_DEVICE_ADDRESS],
                )
                self._connect_error_logged = False
            return {
                "state": self.device.state,
                "device_type": self.device.device_type,
                "name": self.device.name,
                "address": self.device.address,
            }
        except Exception as err:
            _LOGGER.exception("Error updating device state: %s", err)
            # Try to reconnect on error
            self.device = None
            raise UpdateFailed(f"Error communicating with device: {err}") from err

    async def _async_connect(self) -> None:
        """Connect to the device."""
        try:
            address = self.entry.data[CONF_DEVICE_ADDRESS]
            # Normalize address for comparison (uppercase)
            normalized_address = address.upper()
            self._client = StorzBickelClient()

            # Scan and find the device (case-insensitive comparison)
            devices = await self._client.scan(timeout=10.0)
            device_info = next(
                (d for d in devices if d.address.upper() == normalized_address), None
            )

            if not device_info:
                raise UpdateFailed(
                    f"Device {address} not found. Make sure the device is powered on and in range."
                )

            # Connect to the device
            self.device = await self._client.connect_device(device_info)
            self._connect_error_logged = False
            _LOGGER.info("Connected to device %s", self.device.name or address)
        except Exception as err:
            self.device = None
            if not self._connect_error_logged:
                _LOGGER.warning("Error connecting to device: %s", err, exc_info=True)
                self._connect_error_logged = True
            else:
                _LOGGER.debug("Error connecting to device (repeated): %s", err)
            raise UpdateFailed(f"Error connecting to device: {err}") from err

    async def async_connect(self) -> None:
        """Ensure device connection is established."""
        if self.device is not None:
            return
        async with self._connect_lock:
            if self.device is None:
                await self._async_connect()

    async def async_disconnect(self) -> None:
        """Disconnect active device connection."""
        if self.device is None:
            return
        try:
            await self.device.disconnect()
        finally:
            self.device = None

    async def async_reconnect(self) -> None:
        """Force reconnect to the device and refresh state."""
        await self.async_disconnect()
        await self.async_connect()
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self.device:
            try:
                await self.device.disconnect()
            except Exception as err:
                _LOGGER.exception("Error disconnecting device: %s", err)
        await super().async_shutdown()
