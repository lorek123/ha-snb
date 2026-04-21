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
    DOMAIN,
    device_type_slug,
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

    dt = device_type_slug(coordinator.data.get("device_type")) if coordinator.data else None

    # Add air pump switch if device supports it (Volcano Hybrid)
    if dt == DEVICE_TYPE_VOLCANO:
        entities.append(AirPumpSwitch(coordinator))

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
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return False
        state = self.coordinator.data["state"]
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


class VibrationSwitch(StorzBickelEntity, SwitchEntity):
    """Enable/disable vibration (Venty/Veazy)."""

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_vibration"
        self._attr_translation_key = "vibration"

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return False
        state = self.coordinator.data["state"]
        return bool(getattr(state, "vibration_enabled", False))

    async def async_turn_on(self, **kwargs) -> None:
        if self.coordinator.device and hasattr(self.coordinator.device, "set_vibration"):
            await self.coordinator.device.set_vibration(True)
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        if self.coordinator.device and hasattr(self.coordinator.device, "set_vibration"):
            await self.coordinator.device.set_vibration(False)
            await self.coordinator.async_request_refresh()


class SuperboostSwitch(StorzBickelEntity, SwitchEntity):
    """Enable/disable superboost mode on Crafty."""

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_superboost"
        self._attr_translation_key = "superboost"

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return False
        return bool(getattr(self.coordinator.data["state"], "superboost_mode", False))

    async def async_turn_on(self, **kwargs) -> None:
        if self.coordinator.device and hasattr(self.coordinator.device, "set_superboost"):
            await self.coordinator.device.set_superboost(True)
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        if self.coordinator.device and hasattr(self.coordinator.device, "set_superboost"):
            await self.coordinator.device.set_superboost(False)
            await self.coordinator.async_request_refresh()


class BoostTimeoutDisabledSwitch(StorzBickelEntity, SwitchEntity):
    """Enable/disable boost timeout disable flag (Venty/Veazy)."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_boost_timeout_disabled"
        self._attr_translation_key = "boost_timeout_disabled"

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return False
        state = self.coordinator.data["state"]
        return bool(getattr(state, "boost_timeout_disabled", False))

    async def async_turn_on(self, **kwargs) -> None:
        if self.coordinator.device and hasattr(
            self.coordinator.device, "set_boost_timeout_disabled"
        ):
            await self.coordinator.device.set_boost_timeout_disabled(True)
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        if self.coordinator.device and hasattr(
            self.coordinator.device, "set_boost_timeout_disabled"
        ):
            await self.coordinator.device.set_boost_timeout_disabled(False)
            await self.coordinator.async_request_refresh()
