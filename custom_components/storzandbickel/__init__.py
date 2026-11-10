"""The Storz & Bickel integration."""

from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN, RETIRED_ENTITIES
from .coordinator import StorzBickelDataUpdateCoordinator
from .data import StorzBickelRuntimeData

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Storz & Bickel from a config entry."""
    coordinator = StorzBickelDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = StorzBickelRuntimeData(coordinator=coordinator)

    if bluetooth.async_scanner_count(hass, connectable=True) == 0:
        ir.async_create_issue(
            hass,
            DOMAIN,
            "no_connectable_bluetooth",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="no_connectable_bluetooth",
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, "no_connectable_bluetooth")

    _async_remove_retired_entities(hass, entry, coordinator.device_slug())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


def _async_remove_retired_entities(
    hass: HomeAssistant, entry: ConfigEntry, device_slug: str | None
) -> None:
    """Delete registry entries for entities this integration no longer provides."""
    registry = er.async_get(hass)
    for platform, suffix, device_types in RETIRED_ENTITIES:
        if device_types is not None and device_slug not in device_types:
            continue
        entity_id = registry.async_get_entity_id(
            platform, DOMAIN, f"{entry.entry_id}_{suffix}"
        )
        if entity_id is not None:
            registry.async_remove(entity_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        runtime: StorzBickelRuntimeData = entry.runtime_data
        if runtime.coordinator.device is not None:
            await runtime.coordinator.device.disconnect()

    return unload_ok
