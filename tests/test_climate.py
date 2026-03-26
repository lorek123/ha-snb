"""Test the climate platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from storzandbickel_ble.models import DeviceState, DeviceType

from homeassistant.components.climate import HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant

from custom_components.storzandbickel.climate import StorzBickelClimateEntity
from custom_components.storzandbickel.const import DOMAIN
from custom_components.storzandbickel.coordinator import StorzBickelDataUpdateCoordinator


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test-entry"
    entry.title = "Test Device"
    return entry


@pytest.fixture
def mock_device_state():
    """Create a mock device state."""
    state = MagicMock(spec=DeviceState)
    state.current_temperature = 180.0
    state.target_temperature = 185.0
    state.heater_on = True
    return state


@pytest.fixture
def mock_device(mock_device_state):
    """Create a mock device."""
    device = AsyncMock()
    device.state = mock_device_state
    device.set_target_temperature = AsyncMock()
    device.turn_heater_on = AsyncMock()
    device.turn_heater_off = AsyncMock()
    return device


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_entry, mock_device):
    """Create a coordinator with mock device."""
    coordinator = StorzBickelDataUpdateCoordinator(hass, mock_entry)
    coordinator.device = mock_device
    coordinator.data = {
        "state": mock_device.state,
        "device_type": DeviceType.CRAFTY,
        "name": "Test Device",
        "address": "AA:BB:CC:DD:EE:FF",
    }
    return coordinator


class TestStorzBickelClimateEntity:
    """Test the climate entity."""

    def test_initialization(self, coordinator):
        """Test entity initialization."""
        entity = StorzBickelClimateEntity(coordinator)

        assert entity._attr_unique_id == "test-entry_climate"
        assert entity._attr_has_entity_name is True
        assert entity._attr_translation_key == "temperature"
        assert entity._attr_temperature_unit == UnitOfTemperature.CELSIUS
        assert entity._attr_min_temp == 40.0
        assert entity._attr_max_temp == 230.0
        assert entity._attr_target_temperature_step == 1.0
        assert HVACMode.HEAT in entity._attr_hvac_modes
        assert HVACMode.OFF in entity._attr_hvac_modes

    def test_current_temperature(self, coordinator, mock_device_state):
        """Test current temperature property."""
        entity = StorzBickelClimateEntity(coordinator)

        assert entity.current_temperature == 180.0

    def test_current_temperature_none(self, coordinator):
        """Test current temperature when data is None."""
        coordinator.data = None
        entity = StorzBickelClimateEntity(coordinator)

        assert entity.current_temperature is None

    def test_target_temperature(self, coordinator, mock_device_state):
        """Test target temperature property."""
        entity = StorzBickelClimateEntity(coordinator)

        assert entity.target_temperature == 185.0

    def test_target_temperature_none(self, coordinator):
        """Test target temperature when data is None."""
        coordinator.data = None
        entity = StorzBickelClimateEntity(coordinator)

        assert entity.target_temperature is None

    def test_hvac_mode_heat(self, coordinator, mock_device_state):
        """Test HVAC mode when heater is on."""
        entity = StorzBickelClimateEntity(coordinator)

        assert entity.hvac_mode == HVACMode.HEAT

    def test_hvac_mode_off(self, coordinator, mock_device_state):
        """Test HVAC mode when heater is off."""
        mock_device_state.heater_on = False
        entity = StorzBickelClimateEntity(coordinator)

        assert entity.hvac_mode == HVACMode.OFF

    def test_hvac_mode_none(self, coordinator):
        """Test HVAC mode when data is None."""
        coordinator.data = None
        entity = StorzBickelClimateEntity(coordinator)

        assert entity.hvac_mode == HVACMode.OFF

    async def test_set_temperature(self, coordinator, mock_device):
        """Test setting target temperature."""
        entity = StorzBickelClimateEntity(coordinator)

        await entity.async_set_temperature(**{ATTR_TEMPERATURE: 190.0})

        mock_device.set_target_temperature.assert_called_once_with(190.0)

    async def test_set_temperature_no_device(self, coordinator):
        """Test setting temperature when device is None."""
        coordinator.device = None
        entity = StorzBickelClimateEntity(coordinator)

        # Should not raise an error
        await entity.async_set_temperature(**{ATTR_TEMPERATURE: 190.0})

    async def test_set_temperature_no_temperature(self, coordinator):
        """Test setting temperature without temperature parameter."""
        entity = StorzBickelClimateEntity(coordinator)

        # Should not raise an error
        await entity.async_set_temperature()

    async def test_set_hvac_mode_heat(self, coordinator, mock_device):
        """Test setting HVAC mode to heat."""
        entity = StorzBickelClimateEntity(coordinator)

        await entity.async_set_hvac_mode(HVACMode.HEAT)

        mock_device.turn_heater_on.assert_called_once()

    async def test_set_hvac_mode_off(self, coordinator, mock_device):
        """Test setting HVAC mode to off."""
        entity = StorzBickelClimateEntity(coordinator)

        await entity.async_set_hvac_mode(HVACMode.OFF)

        mock_device.turn_heater_off.assert_called_once()

    async def test_set_hvac_mode_no_device(self, coordinator):
        """Test setting HVAC mode when device is None."""
        coordinator.device = None
        entity = StorzBickelClimateEntity(coordinator)

        # Should not raise an error
        await entity.async_set_hvac_mode(HVACMode.HEAT)
