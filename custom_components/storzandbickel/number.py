"""Number platform for Storz & Bickel integration."""

from __future__ import annotations


from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_TYPE_CRAFTY,
    DEVICE_TYPE_VEAZY,
    DEVICE_TYPE_VENTY,
    DEVICE_TYPE_VOLCANO,
)
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
    dt = coordinator.device_slug()

    entities: list[NumberEntity] = []

    if dt in [DEVICE_TYPE_VENTY, DEVICE_TYPE_VEAZY]:
        entities.append(BrightnessNumber(coordinator))
        entities.append(VentyBoostOffsetNumber(coordinator))
        entities.append(VentySuperboostOffsetNumber(coordinator))

    if dt == DEVICE_TYPE_CRAFTY:
        entities.append(CraftyBoostTemperatureNumber(coordinator))
        entities.append(CraftyLedBrightnessNumber(coordinator))
        entities.append(CraftyAutoOffNumber(coordinator))

    if dt == DEVICE_TYPE_VOLCANO:
        entities.append(VolcanoLedBrightnessNumber(coordinator))
        entities.append(VolcanoAutoOffNumber(coordinator))

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
        state = self.device_state
        if state is None:
            return None
        return getattr(state, "brightness", None)

    async def async_set_native_value(self, value: float) -> None:
        await self._async_call_device("set_brightness", int(value))


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
        state = self.device_state
        if state is None:
            return None
        for attr in ("boost_temperature", "boost_temp", "boost_offset"):
            value = getattr(state, attr, None)
            if isinstance(value, (int, float)):
                return float(value)
        return None

    async def async_set_native_value(self, value: float) -> None:
        await self._async_call_device("set_boost_temperature", float(value))


class CraftyLedBrightnessNumber(StorzBickelEntity, NumberEntity):
    """Crafty LED brightness (0-100)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_led_brightness"
        self._attr_translation_key = "led_brightness"

    @property
    def native_value(self) -> float | None:
        state = self.device_state
        if state is None:
            return None
        return getattr(state, "led_brightness", None)

    async def async_set_native_value(self, value: float) -> None:
        await self._async_call_device("set_led_brightness", int(value))


class CraftyAutoOffNumber(StorzBickelEntity, NumberEntity):
    """Crafty auto-off time in seconds (0 = disabled)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0
    _attr_native_max_value = 3600
    _attr_native_step = 30
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_auto_off_time"
        self._attr_translation_key = "auto_off_time"

    @property
    def native_value(self) -> float | None:
        state = self.device_state
        if state is None:
            return None
        return getattr(state, "auto_off_time", None)

    async def async_set_native_value(self, value: float) -> None:
        await self._async_call_device("set_auto_off_time", int(value))


class VolcanoLedBrightnessNumber(StorzBickelEntity, NumberEntity):
    """Volcano display/LED brightness (1-9)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 1
    _attr_native_max_value = 9
    _attr_native_step = 1

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_led_brightness"
        self._attr_translation_key = "led_brightness"

    @property
    def native_value(self) -> float | None:
        state = self.device_state
        if state is None:
            return None
        return getattr(state, "led_brightness", None)

    async def async_set_native_value(self, value: float) -> None:
        await self._async_call_device("set_led_brightness", int(value))


class VolcanoAutoOffNumber(StorzBickelEntity, NumberEntity):
    """Volcano auto-off time in seconds (0 = disabled)."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0
    _attr_native_max_value = 3600
    _attr_native_step = 30
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_auto_off_time"
        self._attr_translation_key = "auto_off_time"

    @property
    def native_value(self) -> float | None:
        state = self.device_state
        if state is None:
            return None
        return getattr(state, "auto_off_time", None)

    async def async_set_native_value(self, value: float) -> None:
        await self._async_call_device("set_auto_off_time", int(value))


class VentyBoostOffsetNumber(StorzBickelEntity, NumberEntity):
    """Venty/Veazy boost temperature offset, in degrees above the base setpoint."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0
    _attr_native_max_value = 99
    _attr_native_step = 1

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_boost_offset"
        self._attr_translation_key = "boost_offset"

    @property
    def native_value(self) -> float | None:
        state = self.device_state
        if state is None:
            return None
        return getattr(state, "boost_offset", None)

    async def async_set_native_value(self, value: float) -> None:
        await self._async_call_device("set_boost_offset", int(value))


class VentySuperboostOffsetNumber(StorzBickelEntity, NumberEntity):
    """Venty/Veazy superboost temperature offset, in degrees above boost."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0
    _attr_native_max_value = 99
    _attr_native_step = 1

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_superboost_offset"
        self._attr_translation_key = "superboost_offset"

    @property
    def native_value(self) -> float | None:
        state = self.device_state
        if state is None:
            return None
        return getattr(state, "superboost_offset", None)

    async def async_set_native_value(self, value: float) -> None:
        await self._async_call_device("set_superboost_offset", int(value))
