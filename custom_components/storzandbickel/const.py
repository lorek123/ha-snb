"""Constants for the Storz & Bickel integration."""
from __future__ import annotations

DOMAIN = "storzandbickel"

# Configuration
CONF_DEVICE_ADDRESS = "device_address"
CONF_DEVICE_NAME = "device_name"
CONF_DEVICE_TYPE = "device_type"

# Device types (normalized slugs)
DEVICE_TYPE_VOLCANO = "volcano"
DEVICE_TYPE_VENTY = "venty"
DEVICE_TYPE_CRAFTY = "crafty"
DEVICE_TYPE_VEAZY = "veazy"


def device_type_slug(device_type: object | None) -> str | None:
    """Normalize storzandbickel_ble DeviceType to a lowercase slug."""
    if device_type is None:
        return None
    # storzandbickel_ble.models.DeviceType is an IntEnum in >=0.1.4
    name_attr = getattr(device_type, "name", None)
    if isinstance(name_attr, str):
        return name_attr.lower()
    # Back-compat with earlier string enums
    value_attr = getattr(device_type, "value", None)
    if isinstance(value_attr, str):
        return value_attr.lower()
    s = str(device_type)
    # Handle "DeviceType.VENTY"
    if "." in s:
        tail = s.split(".")[-1]
        if tail:
            return tail.lower()
    return s.lower()

# Attributes
ATTR_BATTERY_LEVEL = "battery_level"
ATTR_BOOST_MODE = "boost_mode"
ATTR_HEATER_STATE = "heater_state"
ATTR_AIR_PUMP_STATE = "air_pump_state"
ATTR_VIBRATION = "vibration"

# Defaults
DEFAULT_SCAN_TIMEOUT = 10.0
DEFAULT_UPDATE_INTERVAL = 5.0
