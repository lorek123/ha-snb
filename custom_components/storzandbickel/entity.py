"""Base entity for Storz & Bickel integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StorzBickelDataUpdateCoordinator
from .const import device_type_slug


class StorzBickelEntity(CoordinatorEntity[StorzBickelDataUpdateCoordinator], Entity):
    """Base entity for Storz & Bickel entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        device_type = (
            device_type_slug(coordinator.data.get("device_type"))
            if coordinator.data
            else None
        )
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.title,
            manufacturer="Storz & Bickel",
            model=device_type or "Unknown",
        )
