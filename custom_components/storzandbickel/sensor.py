"""Sensor platform for Storz & Bickel integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_TYPE_CRAFTY,
    DEVICE_TYPE_VEAZY,
    DEVICE_TYPE_VENTY,
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
    """Set up the sensor platform."""
    runtime: StorzBickelRuntimeData = entry.runtime_data
    coordinator = runtime.coordinator
    entities: list[SensorEntity] = []

    # Always add temperature sensor
    entities.append(CurrentTemperatureSensor(coordinator))
    entities.append(ConnectionStateSensor(coordinator))
    entities.append(SignalStrengthSensor(coordinator))

    # Add battery sensor if device supports it
    dt = device_type_slug(coordinator.data.get("device_type")) if coordinator.data else None
    if dt in [DEVICE_TYPE_CRAFTY, DEVICE_TYPE_VENTY, DEVICE_TYPE_VEAZY]:
        entities.append(BatteryLevelSensor(coordinator))

    async_add_entities(entities)


class CurrentTemperatureSensor(StorzBickelEntity, SensorEntity):
    """Representation of a current temperature sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.TEMPERATURE

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_current_temperature"
        self._attr_translation_key = "current_temperature"

    @property
    def native_value(self) -> float | None:
        """Return the current temperature."""
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return None
        return self.coordinator.data["state"].current_temperature


class BatteryLevelSensor(StorzBickelEntity, SensorEntity):
    """Representation of a battery level sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.BATTERY

    def __init__(self, coordinator: StorzBickelDataUpdateCoordinator) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_battery"
        self._attr_translation_key = "battery"

    @property
    def native_value(self) -> int | None:
        """Return the battery level."""
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return None
        state = self.coordinator.data["state"]
        if hasattr(state, "battery_level") and state.battery_level is not None:
            return state.battery_level
        return None


class ConnectionStateSensor(StorzBickelEntity, SensorEntity):
    """Connected/disconnected state from coordinator connection."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "connection_state"

    @property
    def native_value(self) -> str:
        """Return connection state."""
        return "connected" if self.coordinator.device is not None else "disconnected"


class SignalStrengthSensor(StorzBickelEntity, SensorEntity):
    """Signal strength if exposed by upstream state."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "signal_strength"
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        """Return signal strength."""
        if not self.coordinator.data or not self.coordinator.data.get("state"):
            return None
        state = self.coordinator.data["state"]
        rssi = getattr(state, "rssi", None)
        return rssi if isinstance(rssi, int) else None
