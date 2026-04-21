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

from .const import DEVICE_TYPE_CRAFTY, device_type_slug
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

    dt = device_type_slug(coordinator.data.get("device_type")) if coordinator.data else None

    if dt == DEVICE_TYPE_CRAFTY:
        entities.append(ChargingBinarySensor(coordinator))

    async_add_entities(entities)


class ChargingBinarySensor(StorzBickelEntity, BinarySensorEntity):
    """Charging status for Crafty."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_charging"
        self._attr_translation_key = "charging"

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return None
        return bool(getattr(self.coordinator.data["state"], "charging", False))
