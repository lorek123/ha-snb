"""Select platform for Storz & Bickel integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from storzandbickel_ble.models import HeaterMode

from .const import DEVICE_TYPE_VEAZY, DEVICE_TYPE_VENTY, DEVICE_TYPE_VOLCANO
from .data import StorzBickelRuntimeData
from .coordinator import StorzBickelDataUpdateCoordinator
from .entity import StorzBickelEntity

VOLCANO_WORKFLOW_PRESETS = ["balloon", "flow1", "flow2", "flow3"]

# Venty/Veazy heater modes a user can pick. Off is owned by the climate entity.
VENTY_HEATER_MODES: dict[str, HeaterMode] = {
    "normal": HeaterMode.NORMAL,
    "boost": HeaterMode.BOOST,
    "superboost": HeaterMode.SUPERBOOST,
}

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    runtime: StorzBickelRuntimeData = entry.runtime_data
    coordinator = runtime.coordinator
    dt = coordinator.device_slug()

    entities: list[SelectEntity] = []
    if dt == DEVICE_TYPE_VOLCANO:
        entities.append(VolcanoWorkflowPresetSelect(coordinator))

    if dt in [DEVICE_TYPE_VENTY, DEVICE_TYPE_VEAZY]:
        entities.append(VentyHeaterModeSelect(coordinator))

    async_add_entities(entities)


class VolcanoWorkflowPresetSelect(StorzBickelEntity, SelectEntity):
    """Run Volcano workflow presets."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = VOLCANO_WORKFLOW_PRESETS

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_workflow_preset"
        self._attr_translation_key = "workflow_preset"

    @property
    def current_option(self) -> str | None:
        # We don't have a device-side "current workflow" state; show None.
        return None

    async def async_select_option(self, option: str) -> None:
        if option not in VOLCANO_WORKFLOW_PRESETS:
            return
        await self._async_call_device("run_workflow_preset", option)


class VentyHeaterModeSelect(StorzBickelEntity, SelectEntity):
    """Select the Venty/Veazy heater mode (normal / boost / superboost).

    Off is owned by the climate entity; this picks the active heating level and
    is the replacement for the Crafty-only boost button on these devices.
    """

    _attr_options = list(VENTY_HEATER_MODES)

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_heater_mode"
        self._attr_translation_key = "heater_mode"

    @property
    def current_option(self) -> str | None:
        state = self.device_state
        if state is None:
            return None
        mode = getattr(state, "heater_mode", None)
        for name, value in VENTY_HEATER_MODES.items():
            if mode == value:
                return name
        return None

    async def async_select_option(self, option: str) -> None:
        mode = VENTY_HEATER_MODES.get(option)
        if mode is None:
            return
        await self._async_call_device("set_heater_mode", mode)
