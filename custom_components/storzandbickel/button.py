"""Button platform for Storz & Bickel integration."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .data import StorzBickelRuntimeData
from .coordinator import StorzBickelDataUpdateCoordinator
from .entity import StorzBickelEntity
from .const import DEVICE_TYPE_CRAFTY, DEVICE_TYPE_VEAZY, DEVICE_TYPE_VENTY, device_type_slug

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    runtime: StorzBickelRuntimeData = entry.runtime_data
    coordinator = runtime.coordinator
    entities: list[ButtonEntity] = [
        ReconnectButton(coordinator),
        RefreshButton(coordinator),
    ]

    dt = device_type_slug(coordinator.data.get("device_type")) if coordinator.data else None
    if dt in [DEVICE_TYPE_CRAFTY, DEVICE_TYPE_VENTY, DEVICE_TYPE_VEAZY]:
        entities.append(BoostModeButton(coordinator))
        entities.append(FindDeviceButton(coordinator))

    async_add_entities(entities)


class BoostModeButton(StorzBickelEntity, ButtonEntity):
    """Representation of a boost mode button."""

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        """Initialize the boost mode button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_boost"
        self._attr_translation_key = "boost_mode"

    async def async_press(self) -> None:
        """Handle the button press."""
        if self.coordinator.device and hasattr(self.coordinator.device, "activate_boost_mode"):
            await self.coordinator.device.activate_boost_mode()
            await self.coordinator.async_request_refresh()


class FindDeviceButton(StorzBickelEntity, ButtonEntity):
    """Trigger find-device alert (vibration/LED)."""

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_find_device"
        self._attr_translation_key = "find_device"

    async def async_press(self) -> None:
        if self.coordinator.device and hasattr(self.coordinator.device, "find_device"):
            await self.coordinator.device.find_device()


class ReconnectButton(StorzBickelEntity, ButtonEntity):
    """Reconnect to the BLE device."""

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        """Initialize reconnect button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_reconnect"
        self._attr_translation_key = "reconnect"

    async def async_press(self) -> None:
        """Reconnect and refresh."""
        await self.coordinator.async_reconnect()


class RefreshButton(StorzBickelEntity, ButtonEntity):
    """Request an immediate state refresh."""

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        """Initialize refresh button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_refresh"
        self._attr_translation_key = "refresh"

    async def async_press(self) -> None:
        """Request coordinator refresh."""
        await self.coordinator.async_request_refresh()
