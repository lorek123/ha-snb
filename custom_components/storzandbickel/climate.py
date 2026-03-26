"""Climate platform for Storz & Bickel integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import StorzBickelRuntimeData
from .coordinator import StorzBickelDataUpdateCoordinator
from .entity import StorzBickelEntity

# Temperature ranges based on device type
TEMP_MIN = 40.0
TEMP_MAX = 230.0
TEMP_STEP = 1.0

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the climate platform."""
    runtime: StorzBickelRuntimeData = entry.runtime_data
    coordinator = runtime.coordinator
    async_add_entities([StorzBickelClimateEntity(coordinator)])


class StorzBickelClimateEntity(StorzBickelEntity, ClimateEntity):
    """Representation of a Storz & Bickel climate entity."""

    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = TEMP_MIN
    _attr_max_temp = TEMP_MAX
    _attr_target_temperature_step = TEMP_STEP

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_climate"
        self._attr_translation_key = "temperature"

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return None
        return self.coordinator.data["state"].current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return None
        return self.coordinator.data["state"].target_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return HVACMode.OFF
        state = self.coordinator.data["state"]
        if state.heater_on:
            return HVACMode.HEAT
        return HVACMode.OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        if self.coordinator.device:
            await self.coordinator.device.set_target_temperature(temperature)
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target HVAC mode."""
        if not self.coordinator.device:
            return

        if hvac_mode == HVACMode.HEAT:
            await self.coordinator.device.turn_heater_on()
        elif hvac_mode == HVACMode.OFF:
            await self.coordinator.device.turn_heater_off()

        await self.coordinator.async_request_refresh()
