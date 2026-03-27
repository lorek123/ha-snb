"""Number platform for Storz & Bickel integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_CRAFTY, DEVICE_TYPE_VEAZY, DEVICE_TYPE_VENTY, DOMAIN, device_type_slug
from .data import StorzBickelRuntimeData
from .coordinator import StorzBickelDataUpdateCoordinator
from .entity import StorzBickelEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""
    runtime: StorzBickelRuntimeData = entry.runtime_data
    coordinator = runtime.coordinator
    dt = device_type_slug(coordinator.data.get("device_type")) if coordinator.data else None

    entities: list[NumberEntity] = []

    if dt in [DEVICE_TYPE_VENTY, DEVICE_TYPE_VEAZY]:
        entities.append(BrightnessNumber(coordinator))

    if dt == DEVICE_TYPE_CRAFTY:
        entities.append(CraftyBoostTemperatureNumber(coordinator))

    async_add_entities(entities)


class BrightnessNumber(StorzBickelEntity, NumberEntity):
    """Venty/Veazy brightness (1-9)."""

    _attr_native_min_value = 1
    _attr_native_max_value = 9
    _attr_native_step = 1

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_brightness"
        self._attr_translation_key = "brightness"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return None
        return getattr(self.coordinator.data["state"], "brightness", None)

    async def async_set_native_value(self, value: float) -> None:
        if self.coordinator.device and hasattr(self.coordinator.device, "set_brightness"):
            await self.coordinator.device.set_brightness(int(value))
            await self.coordinator.async_request_refresh()


class CraftyBoostTemperatureNumber(StorzBickelEntity, NumberEntity):
    """Crafty boost temperature setting."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 1
    _attr_native_max_value = 99
    _attr_native_step = 1

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_boost_temperature"
        self._attr_translation_key = "boost_temperature"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return None
        state = self.coordinator.data["state"]
        for attr in ("boost_temperature", "boost_temp", "boost_offset"):
            value = getattr(state, attr, None)
            if isinstance(value, (int, float)):
                return float(value)
        return None

    async def async_set_native_value(self, value: float) -> None:
        if not self.coordinator.device:
            return

        device = self.coordinator.device
        device_dict = getattr(device, "__dict__", {})

        # Compatibility with potential upstream method rename.
        if "set_boost_offset" in device_dict or hasattr(type(device), "set_boost_offset"):
            await device.set_boost_offset(float(value))
            await self.coordinator.async_request_refresh()
            return

        if "set_boost_temperature" in device_dict or hasattr(
            type(device), "set_boost_temperature"
        ):
            await device.set_boost_temperature(float(value))
            await self.coordinator.async_request_refresh()

