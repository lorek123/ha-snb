"""Binary sensor platform for Storz & Bickel integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_CRAFTY, DEVICE_TYPE_VEAZY, DEVICE_TYPE_VENTY
from .coordinator import StorzBickelDataUpdateCoordinator
from .data import StorzBickelRuntimeData
from .entity import StorzBickelEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    runtime: StorzBickelRuntimeData = entry.runtime_data
    coordinator = runtime.coordinator
    entities: list[BinarySensorEntity] = []

    dt = coordinator.device_slug()

    if dt in [DEVICE_TYPE_VENTY, DEVICE_TYPE_VEAZY]:
        entities.append(VentyChargingBinarySensor(coordinator))

    if dt in [DEVICE_TYPE_CRAFTY, DEVICE_TYPE_VENTY, DEVICE_TYPE_VEAZY]:
        entities.append(ReadyBinarySensor(coordinator))

    async_add_entities(entities)


class VentyChargingBinarySensor(StorzBickelEntity, BinarySensorEntity):
    """Charging status for Venty/Veazy (reads charger_connected)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_charging"
        self._attr_translation_key = "charging"

    @property
    def is_on(self) -> bool | None:
        state = self.device_state
        if state is None:
            return None
        charging = getattr(state, "charger_connected", None)
        return bool(charging) if charging is not None else None


class ReadyBinarySensor(StorzBickelEntity, BinarySensorEntity):
    """Setpoint reached / ready to use (Crafty/Venty/Veazy)."""

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_ready"
        self._attr_translation_key = "ready"

    @property
    def is_on(self) -> bool | None:
        state = self.device_state
        if state is None:
            return None
        return bool(getattr(state, "setpoint_reached", False))
