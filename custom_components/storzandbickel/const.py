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

# Entities removed in past releases, as (platform, unique-id suffix, device types).
# HA keeps retired entities in the registry as "unavailable" until deleted by hand,
# so setup removes them. A device-type set of None means "every device".
RETIRED_ENTITIES: tuple[tuple[str, str, frozenset[str] | None], ...] = (
    # Crafty boost button / superboost switch -> read-only binary sensors (0.1.29);
    # the Venty boost button was dropped earlier.
    ("button", "boost", None),
    ("switch", "superboost", None),
    # Crafty charging sensor (never decoded). Venty/Veazy still have "charging".
    (
        "binary_sensor",
        "charging",
        frozenset({DEVICE_TYPE_CRAFTY, DEVICE_TYPE_VOLCANO}),
    ),
)


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
