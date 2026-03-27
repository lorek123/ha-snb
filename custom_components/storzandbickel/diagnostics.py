"""Diagnostics support."""

from __future__ import annotations

import importlib.metadata
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ADDRESS, CONF_DEVICE_NAME, CONF_DEVICE_TYPE
from .data import StorzBickelRuntimeData


def _redact_address(address: str) -> str:
    """Keep only the last three octets for support context (MAC is not secret but privacy-friendly)."""
    if ":" in address:
        parts = address.upper().split(":")
        if len(parts) == 6:
            return "**:**:**:**:" + ":".join(parts[-3:])
    if "-" in address:
        parts = address.upper().split("-")
        if len(parts) == 6:
            return "**-**-**-**-" + "-".join(parts[-3:])
    return "***"


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    lib_ver: str | None
    try:
        lib_ver = importlib.metadata.version("storzandbickel-ble")
    except importlib.metadata.PackageNotFoundError:
        lib_ver = None

    base: dict[str, Any] = {
        "title": entry.title,
        "device_name": entry.data.get(CONF_DEVICE_NAME),
        "device_type": entry.data.get(CONF_DEVICE_TYPE),
        "device_address_tail": _redact_address(str(entry.data.get(CONF_DEVICE_ADDRESS, ""))),
        "library_version": lib_ver,
        "connection_state": "disconnected",
    }

    runtime_data = getattr(entry, "runtime_data", None)
    if runtime_data is None:
        base["coordinator_device_connected"] = False
        return base

    runtime: StorzBickelRuntimeData = runtime_data
    coord = runtime.coordinator
    base["coordinator_device_connected"] = coord.device is not None
    base["last_update_success"] = coord.last_update_success
    base["connection_state"] = "connected" if coord.device is not None else "disconnected"
    if coord.last_exception is not None:
        base["last_exception"] = repr(coord.last_exception)

    device = coord.device
    if device is not None:
        for attr in ("name", "address", "device_type", "firmware_version", "ble_firmware_version", "serial_number"):
            value = getattr(device, attr, None)
            if value is not None:
                if attr == "address":
                    base["device_address_tail_live"] = _redact_address(str(value))
                elif attr == "device_type":
                    base["device_type_live"] = str(value)
                else:
                    base[attr] = str(value)

    if coord.data and coord.data.get("state"):
        state = coord.data["state"]
        for attr in ("rssi", "hours", "minutes", "battery_level"):
            value = getattr(state, attr, None)
            if value is not None:
                base[f"state_{attr}"] = value

    return base
