"""Select platform for Storz & Bickel integration."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_VOLCANO, DOMAIN, device_type_slug
from .data import StorzBickelRuntimeData
from .coordinator import StorzBickelDataUpdateCoordinator
from .entity import StorzBickelEntity

VOLCANO_WORKFLOW_PRESETS = ["balloon", "flow1", "flow2", "flow3"]

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    runtime: StorzBickelRuntimeData = entry.runtime_data
    coordinator = runtime.coordinator
    dt = device_type_slug(coordinator.data.get("device_type")) if coordinator.data else None

    entities: list[SelectEntity] = []
    if dt == DEVICE_TYPE_VOLCANO:
        entities.append(VolcanoWorkflowPresetSelect(coordinator))

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
        if self.coordinator.device and hasattr(self.coordinator.device, "run_workflow_preset"):
            await self.coordinator.device.run_workflow_preset(option)
            await self.coordinator.async_request_refresh()

