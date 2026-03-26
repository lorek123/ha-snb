"""Config flow for Storz & Bickel integration."""
from __future__ import annotations

import logging
import re
from typing import Any, cast

from storzandbickel_ble import StorzBickelClient
from storzandbickel_ble.models import DeviceType
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_NAME,
    CONF_DEVICE_TYPE,
    DOMAIN,
    device_type_slug,
)

_LOGGER = logging.getLogger(__name__)

# MAC address validation pattern (supports both formats: XX:XX:XX:XX:XX:XX and XX-XX-XX-XX-XX-XX)
MAC_ADDRESS_PATTERN = re.compile(
    r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
)


def validate_mac_address(address: str) -> bool:
    """Validate MAC address format."""
    return bool(MAC_ADDRESS_PATTERN.match(address))


def normalize_mac_address(address: str) -> str:
    """Normalize MAC address to uppercase with colons."""
    # Remove any separators and convert to uppercase
    normalized = re.sub(r"[:-]", "", address.upper())
    # Add colons every 2 characters
    return ":".join(normalized[i : i + 2] for i in range(0, len(normalized), 2))


async def validate_input(
    hass: HomeAssistant, data: dict[str, Any], skip_scan: bool = False
) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    address = data[CONF_DEVICE_ADDRESS]
    
    # Normalize MAC address
    address = normalize_mac_address(address)
    
    client = StorzBickelClient()
    
    if skip_scan:
        # For manual entry, we'll try to connect directly
        # We'll validate the device type when we connect
        return {
            CONF_DEVICE_NAME: data.get(CONF_DEVICE_NAME, address),
            CONF_DEVICE_ADDRESS: address,
            CONF_DEVICE_TYPE: data.get(CONF_DEVICE_TYPE, "unknown"),
        }
    
    # For scanned devices, verify it's still available
    devices = await client.scan(timeout=5.0)
    device = next((d for d in devices if d.address.upper() == address.upper()), None)

    if not device:
        raise ValueError("Device not found")

    return {
        CONF_DEVICE_NAME: device.name or device.address,
        CONF_DEVICE_ADDRESS: device.address,
        CONF_DEVICE_TYPE: device_type_slug(device.device_type) or "unknown",
    }


class StorzBickelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Storz & Bickel."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovered_devices: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - choose between scan or manual entry."""
        if user_input is not None:
            if user_input.get("setup_method") == "manual":
                return await self.async_step_manual()
            # Continue with scan
            return await self.async_step_scan()

        # Check if bluetooth is available
        if not bluetooth.async_scanner_count(self.hass, connectable=True):
            # If bluetooth not available, go directly to manual entry
            return await self.async_step_manual()

        schema = vol.Schema(
            {
                vol.Required("setup_method", default="scan"): vol.In(
                    {
                        "scan": "Scan for devices",
                        "manual": "Enter MAC address manually",
                    }
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )

    async def async_step_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the scan step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input, skip_scan=False)
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = str(ex)
            else:
                await self.async_set_unique_id(info[CONF_DEVICE_ADDRESS])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info[CONF_DEVICE_NAME],
                    data=info,
                )

        # Scan for devices
        if not self.discovered_devices:
            try:
                client = StorzBickelClient()
                devices = await client.scan(timeout=10.0)
                self.discovered_devices = {
                    device.address: device.name or device.address for device in devices
                }
            except Exception as ex:
                _LOGGER.exception("Error scanning for devices: %s", ex)
                errors["base"] = "scan_failed"

        if not self.discovered_devices:
            return self.async_show_form(
                step_id="scan",
                errors=errors or {"base": "no_devices_found"},
                description_placeholders={"count": "0"},
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ADDRESS): vol.In(self.discovered_devices),
            }
        )

        return self.async_show_form(
            step_id="scan",
            data_schema=schema,
            errors=errors,
            description_placeholders={"count": str(len(self.discovered_devices))},
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual MAC address entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input.get(CONF_DEVICE_ADDRESS, "").strip()
            
            # Validate MAC address format
            if not validate_mac_address(address):
                errors[CONF_DEVICE_ADDRESS] = "invalid_mac_address"
            else:
                # Normalize the address
                normalized_address = normalize_mac_address(address)
                
                # Check if already configured
                await self.async_set_unique_id(normalized_address)
                self._abort_if_unique_id_configured()
                
                # Try to validate by attempting to connect
                try:
                    # For manual entry, we'll allow it even if device is not currently discoverable
                    # The coordinator will handle connection when the device is available
                    device_name = user_input.get(CONF_DEVICE_NAME, normalized_address)
                    
                    # Try to scan to get device info if available
                    client = StorzBickelClient()
                    devices = await client.scan(timeout=5.0)
                    device = next(
                        (d for d in devices if d.address.upper() == normalized_address.upper()),
                        None,
                    )
                    
                    if device:
                        # Device found, use its info
                        device_type = device_type_slug(device.device_type) or "unknown"
                        device_name = device.name or device_name
                    else:
                        # Device not found, but allow manual entry
                        # We'll try to detect device type on first connection
                        device_type = "unknown"
                        _LOGGER.warning(
                            "Device %s not found during scan, but allowing manual entry",
                            normalized_address,
                        )
                    
                    info = {
                        CONF_DEVICE_NAME: device_name,
                        CONF_DEVICE_ADDRESS: normalized_address,
                        CONF_DEVICE_TYPE: device_type,
                    }
                    
                    return self.async_create_entry(
                        title=info[CONF_DEVICE_NAME],
                        data=info,
                    )
                except Exception as ex:
                    _LOGGER.exception("Unexpected exception: %s", ex)
                    errors["base"] = str(ex)

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ADDRESS): str,
                vol.Optional(CONF_DEVICE_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="manual",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "format": "XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX"
            },
        )

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._async_abort_entries_match({CONF_DEVICE_ADDRESS: discovery_info.address})

        # Check if this is a Storz & Bickel device
        client = StorzBickelClient()
        devices = await client.scan(timeout=5.0)
        device = next(
            (d for d in devices if d.address == discovery_info.address), None
        )

        if not device:
            return self.async_abort(reason="not_supported")

        # Store device info in context (extensions beyond ConfigFlowContext TypedDict)
        ctx = cast(dict[str, Any], self.context)
        ctx["device_address"] = discovery_info.address
        ctx["device_name"] = device.name or discovery_info.name or discovery_info.address

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        ctx = cast(dict[str, Any], self.context)
        if user_input is None:
            device_name = ctx.get("device_name", "Unknown Device")
            return self.async_show_form(
                step_id="bluetooth_confirm",
                description_placeholders={"name": device_name},
            )

        return await self.async_step_scan(
            {
                CONF_DEVICE_ADDRESS: ctx["device_address"],
            }
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update the device name shown in Home Assistant."""
        entry = self._get_reconfigure_entry()
        if user_input is None:
            return self.async_show_form(
                step_id="reconfigure",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_DEVICE_NAME,
                            default=entry.data.get(CONF_DEVICE_NAME) or entry.title,
                        ): str,
                    }
                ),
            )
        name = (user_input.get(CONF_DEVICE_NAME) or "").strip()
        if not name:
            name = str(entry.data[CONF_DEVICE_ADDRESS])
        return self.async_update_and_abort(
            entry,
            title=name,
            data_updates={CONF_DEVICE_NAME: name},
        )
