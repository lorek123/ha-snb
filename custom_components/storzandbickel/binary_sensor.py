"""Binary sensor platform for Storz & Bickel integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.binary_sensor.const import BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_CRAFTY, DEVICE_TYPE_VEAZY, DEVICE_TYPE_VENTY
from .coordinator import StorzBickelDataUpdateCoordinator
from .data import StorzBickelRuntimeData
from .entity import StorzBickelEntity

PARALLEL_UPDATES = 1

# Degrees below target that still count as "ready" when the device flag is unset.
READY_TOLERANCE = 1.0


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

    if dt == DEVICE_TYPE_CRAFTY:
        entities.append(CraftyChargingBinarySensor(coordinator))
        entities.append(CraftyBoostActiveBinarySensor(coordinator))
        entities.append(CraftySuperboostActiveBinarySensor(coordinator))

    async_add_entities(entities)


class VentyChargingBinarySensor(StorzBickelEntity, BinarySensorEntity):
    """Charging status for Venty/Veazy (reads charger_connected)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING
    _state_attr = "charger_connected"

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_charging"
        self._attr_translation_key = "charging"

    @property
    def is_on(self) -> bool | None:
        state = self.device_state
        if state is None:
            return None
        charging = getattr(state, self._state_attr, None)
        return bool(charging) if charging is not None else None


class CraftyChargingBinarySensor(VentyChargingBinarySensor):
    """Crafty charging: charger connected and battery not yet full.

    Matches the device LED (blinking while charging, solid when full). Same unique
    ID as the Crafty charging sensor removed in an earlier release, so existing
    entities come back.
    """

    _state_attr = "charging"


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
        if getattr(state, "setpoint_reached", False) is True:
            return True
        # Fallback: some firmware never sets (or only pulses) the setpoint-reached
        # flag, so also treat "heating and within 1 degree of target" as ready.
        heater_on = getattr(state, "heater_on", None)
        current = getattr(state, "current_temperature", None)
        target = getattr(state, "target_temperature", None)
        if (
            heater_on is True
            and isinstance(current, (int, float))
            and isinstance(target, (int, float))
        ):
            return current >= target - READY_TOLERANCE
        return False


class _CraftyBoostFlagBinarySensor(StorzBickelEntity, BinarySensorEntity):
    """Boost state reported by the Crafty (set with the device button only)."""

    _state_attr: str

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{self._state_attr}"
        self._attr_translation_key = self._state_attr

    @property
    def is_on(self) -> bool | None:
        state = self.device_state
        if state is None:
            return None
        return bool(getattr(state, self._state_attr, False))


class CraftyBoostActiveBinarySensor(_CraftyBoostFlagBinarySensor):
    """Crafty boost mode active."""

    _state_attr = "boost_mode"


class CraftySuperboostActiveBinarySensor(_CraftyBoostFlagBinarySensor):
    """Crafty superboost mode active."""

    _state_attr = "superboost_mode"
