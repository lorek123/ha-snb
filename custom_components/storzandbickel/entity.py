"""Base entity for Storz & Bickel integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ADDRESS, DOMAIN, device_type_slug
from .coordinator import StorzBickelDataUpdateCoordinator


class StorzBickelEntity(CoordinatorEntity[StorzBickelDataUpdateCoordinator], Entity):
    """Base entity for Storz & Bickel entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

    @property
    def device_state(self) -> Any:
        """Return the latest device state object, or None if not yet polled.

        Centralizes the `coordinator.data` / `"state"` presence check that every
        read-only entity property would otherwise repeat.
        """
        data = self.coordinator.data
        return data.get("state") if data else None

    async def _async_call_device(
        self, method: str, *args: Any, refresh: bool = True
    ) -> None:
        """Call a device coroutine by name if present, then refresh.

        Almost every action entity follows the same shape: confirm the device is
        connected and actually exposes the method (it varies by model and library
        version, hence the `hasattr` guard), await it, then ask the coordinator to
        refresh so the new state lands. Centralizing it keeps each feature down to a
        single declarative line. Pass refresh=False for fire-and-forget actions
        (e.g. find-device) that don't change polled state.
        """
        device = self.coordinator.device
        if device is None or not hasattr(device, method):
            return
        await getattr(device, method)(*args)
        if refresh:
            await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        """Return dynamic device info for richer Device page details."""
        data = self.coordinator.data or {}
        device = self.coordinator.device
        address = str(
            data.get("address")
            or getattr(device, "address", None)
            or self.coordinator.entry.data.get(CONF_DEVICE_ADDRESS, "")
        ).upper()
        model = device_type_slug(data.get("device_type")) or "Unknown"
        serial_number = getattr(device, "serial_number", None)
        firmware_version = getattr(device, "firmware_version", None)
        ble_firmware = getattr(device, "ble_firmware_version", None)
        sw_version = (
            f"{firmware_version} (BLE {ble_firmware})"
            if firmware_version and ble_firmware
            else firmware_version or ble_firmware
        )

        info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=self.coordinator.entry.title,
            manufacturer="Storz & Bickel",
            model=model,
        )
        if address:
            info["connections"] = {(CONNECTION_NETWORK_MAC, address)}
        if serial_number:
            info["serial_number"] = str(serial_number)
        if sw_version:
            info["sw_version"] = str(sw_version)
        return info
