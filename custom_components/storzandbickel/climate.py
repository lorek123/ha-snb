"""Climate platform for Storz & Bickel integration."""

from __future__ import annotations

from typing import Any, ClassVar

import voluptuous as vol
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from storzandbickel_ble.models import HeaterMode, VentyState

from .coordinator import StorzBickelDataUpdateCoordinator
from .data import StorzBickelRuntimeData
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

    platform = entity_platform.async_get_current_platform()
    # On-demand device diagnostics report, returned as action response data.
    platform.async_register_entity_service(
        "run_analysis",
        {},
        "async_run_analysis",
        supports_response=SupportsResponse.ONLY,
    )
    # Custom Volcano workflow: a sequence of timed heat+pump steps.
    platform.async_register_entity_service(
        "run_workflow",
        {
            vol.Required("steps"): [
                {
                    vol.Required("temperature"): vol.All(
                        vol.Coerce(float), vol.Range(min=TEMP_MIN, max=TEMP_MAX)
                    ),
                    vol.Optional("hold_seconds", default=0): vol.All(
                        vol.Coerce(float), vol.Range(min=0)
                    ),
                    vol.Optional("pump_seconds", default=5): vol.All(
                        vol.Coerce(float), vol.Range(min=0)
                    ),
                }
            ],
        },
        "async_run_workflow",
    )


class StorzBickelClimateEntity(StorzBickelEntity, ClimateEntity):
    """Representation of a Storz & Bickel climate entity."""

    _attr_hvac_modes: ClassVar[list[HVACMode]] = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
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
        state = self.device_state
        if state is None:
            return None
        return state.current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        state = self.device_state
        if state is None:
            return None
        return state.target_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        state = self.device_state
        if state is None:
            return HVACMode.OFF
        if isinstance(state, VentyState):
            return (
                HVACMode.HEAT if state.heater_mode != HeaterMode.OFF else HVACMode.OFF
            )
        return HVACMode.HEAT if state.heater_on else HVACMode.OFF

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

    async def async_run_analysis(self) -> ServiceResponse:
        """Run the device's on-board diagnostics and return the report.

        Backs the `storzandbickel.run_analysis` action. Returns the library's
        analysis dict (ok/warnings/errors/findings/diagnostics) as response data.
        """
        device = self.coordinator.device
        if device is None:
            raise HomeAssistantError("Device is not connected")
        return await device.run_analysis()

    async def async_run_workflow(self, steps: list[dict[str, float]]) -> None:
        """Run a custom Volcano workflow (timed heat+pump steps).

        Backs the `storzandbickel.run_workflow` action. Blocks until the sequence
        finishes (like the workflow-preset select), so callers can await
        completion or run it from a script.
        """
        device = self.coordinator.device
        if device is None:
            raise HomeAssistantError("Device is not connected")
        if not hasattr(device, "run_workflow"):
            raise HomeAssistantError("Workflows are only supported on the Volcano")
        await device.run_workflow(
            [(s["temperature"], s["hold_seconds"], s["pump_seconds"]) for s in steps]
        )
