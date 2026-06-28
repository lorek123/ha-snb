"""Switch platform for Storz & Bickel integration."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_TYPE_CRAFTY,
    DEVICE_TYPE_VOLCANO,
    DEVICE_TYPE_VENTY,
    DEVICE_TYPE_VEAZY,
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
    """Set up the switch platform."""
    runtime: StorzBickelRuntimeData = entry.runtime_data
    coordinator = runtime.coordinator
    entities: list[SwitchEntity] = []

    dt = coordinator.device_slug()

    # Add air pump switch if device supports it (Volcano Hybrid)
    if dt == DEVICE_TYPE_VOLCANO:
        entities.append(AirPumpSwitch(coordinator))
        entities.append(DisplayOnCoolingSwitch(coordinator))
        entities.append(VibrationOnReadySwitch(coordinator))

    if dt in [DEVICE_TYPE_CRAFTY, DEVICE_TYPE_VENTY, DEVICE_TYPE_VEAZY]:
        entities.append(VibrationSwitch(coordinator))

    if dt in [DEVICE_TYPE_VENTY, DEVICE_TYPE_VEAZY]:
        entities.append(BoostTimeoutDisabledSwitch(coordinator))

    if dt == DEVICE_TYPE_CRAFTY:
        entities.append(SuperboostSwitch(coordinator))

    async_add_entities(entities)


class AirPumpSwitch(StorzBickelEntity, SwitchEntity):
    """Representation of an air pump switch."""

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        """Initialize the air pump switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_air_pump"
        self._attr_translation_key = "air_pump"

    @property
    def is_on(self) -> bool:
        """Return if the air pump is on."""
        state = self.device_state
        if state is None:
            return False
        if hasattr(state, "pump_on"):
            return bool(state.pump_on)
        # Legacy alias if state ever exposes air_pump_on
        if hasattr(state, "air_pump_on"):
            return bool(state.air_pump_on)
        return False

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the air pump on."""
        device = self.coordinator.device
        if not device:
            return
        if hasattr(device, "turn_pump_on"):
            await device.turn_pump_on()
        elif hasattr(device, "turn_air_pump_on"):
            await device.turn_air_pump_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the air pump off."""
        device = self.coordinator.device
        if not device:
            return
        if hasattr(device, "turn_pump_off"):
            await device.turn_pump_off()
        elif hasattr(device, "turn_air_pump_off"):
            await device.turn_air_pump_off()
        await self.coordinator.async_request_refresh()


class _FlagSwitch(StorzBickelEntity, SwitchEntity):
    """Base for boolean device flags read from state and toggled via a setter.

    Vibration, superboost, and boost-timeout are the same switch wearing different
    labels: read one boolean off the coordinator state, write it with one device
    coroutine. Subclasses declare the three names below; all the plumbing —
    presence guard, getattr read, guarded setter call — lives here once.
    """

    _flag_key: str  # config-entry unique-id suffix and translation key
    _state_attr: str  # attribute read from the coordinator state object
    _setter: str  # device coroutine that writes the flag

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{self._flag_key}"
        self._attr_translation_key = self._flag_key

    @property
    def is_on(self) -> bool:
        state = self.device_state
        if state is None:
            return False
        return bool(getattr(state, self._state_attr, False))

    async def async_turn_on(self, **kwargs) -> None:
        await self._async_call_device(self._setter, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_call_device(self._setter, False)


class VibrationSwitch(_FlagSwitch):
    """Enable/disable vibration (Venty/Veazy)."""

    _flag_key = "vibration"
    _state_attr = "vibration_enabled"
    _setter = "set_vibration"


class SuperboostSwitch(_FlagSwitch):
    """Enable/disable superboost mode on Crafty."""

    _flag_key = "superboost"
    _state_attr = "superboost_mode"
    _setter = "set_superboost"


class BoostTimeoutDisabledSwitch(_FlagSwitch):
    """Enable/disable boost timeout disable flag (Venty/Veazy)."""

    _attr_entity_category = EntityCategory.CONFIG
    _flag_key = "boost_timeout_disabled"
    _state_attr = "boost_timeout_disabled"
    _setter = "set_boost_timeout_disabled"


class DisplayOnCoolingSwitch(_FlagSwitch):
    """Show the temperature on the display during cool-down (Volcano)."""

    _attr_entity_category = EntityCategory.CONFIG
    _flag_key = "display_on_cooling"
    _state_attr = "display_on_cooling"
    _setter = "set_display_on_cooling"


class VibrationOnReadySwitch(_FlagSwitch):
    """Vibrate when the setpoint temperature is reached (Volcano)."""

    _attr_entity_category = EntityCategory.CONFIG
    _flag_key = "vibration_on_ready"
    _state_attr = "vibration_on_ready"
    _setter = "set_vibration_on_ready"
