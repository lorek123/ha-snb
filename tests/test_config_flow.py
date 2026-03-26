"""Test the config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from storzandbickel_ble import StorzBickelClient
from storzandbickel_ble.models import DeviceType

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Note: bluetooth is not imported here to avoid dependency issues
# It's patched in tests where needed

from custom_components.storzandbickel.config_flow import (
    StorzBickelConfigFlow,
    normalize_mac_address,
    validate_input,
    validate_mac_address,
)
from custom_components.storzandbickel.const import (
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_NAME,
    CONF_DEVICE_TYPE,
    DOMAIN,
)


@pytest.fixture
def mock_client(mock_device_info):
    """Mock StorzBickelClient."""
    client = AsyncMock(spec=StorzBickelClient)
    client.scan = AsyncMock(return_value=[mock_device_info])
    return client


class TestMACAddressValidation:
    """Test MAC address validation functions."""

    def test_validate_mac_address_valid_colon(self):
        """Test valid MAC address with colons."""
        assert validate_mac_address("AA:BB:CC:DD:EE:FF") is True

    def test_validate_mac_address_valid_dash(self):
        """Test valid MAC address with dashes."""
        assert validate_mac_address("AA-BB-CC-DD-EE-FF") is True

    def test_validate_mac_address_invalid(self):
        """Test invalid MAC address."""
        assert validate_mac_address("invalid") is False
        assert validate_mac_address("AA:BB:CC:DD:EE") is False
        assert validate_mac_address("AA:BB:CC:DD:EE:FF:GG") is False

    def test_normalize_mac_address_colon(self):
        """Test normalizing MAC address with colons."""
        assert normalize_mac_address("aa:bb:cc:dd:ee:ff") == "AA:BB:CC:DD:EE:FF"

    def test_normalize_mac_address_dash(self):
        """Test normalizing MAC address with dashes."""
        assert normalize_mac_address("aa-bb-cc-dd-ee-ff") == "AA:BB:CC:DD:EE:FF"

    def test_normalize_mac_address_no_separator(self):
        """Test normalizing MAC address without separators."""
        assert normalize_mac_address("aabbccddeeff") == "AA:BB:CC:DD:EE:FF"


class TestConfigFlow:
    """Test the config flow."""

    async def test_user_step_choose_method(self, hass: HomeAssistant, mock_bluetooth_scanner):
        """Test initial user step shows method selection."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert "setup_method" in result["data_schema"].schema

    async def test_user_step_no_bluetooth_goes_to_manual(
        self, hass: HomeAssistant
    ):
        """Test that missing bluetooth goes directly to manual entry."""
        with patch(
            "homeassistant.components.bluetooth.async_scanner_count",
            return_value=0,
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "manual"

    async def test_scan_step_no_devices_found(
        self, hass: HomeAssistant, mock_bluetooth_scanner
    ):
        """Test scan step when no devices are found."""
        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = []

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"setup_method": "scan"}
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "scan"
            assert result["errors"]["base"] == "no_devices_found"

    async def test_scan_step_device_found(
        self, hass: HomeAssistant, mock_bluetooth_scanner, mock_device_info
    ):
        """Test scan step when device is found."""
        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            mock_device_info.address = "AA:BB:CC:DD:EE:FF"
            mock_device_info.name = "Test Device"
            mock_device_info.device_type = DeviceType.CRAFTY
            mock_scan.return_value = [mock_device_info]

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"setup_method": "scan"}
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "scan"
            assert CONF_DEVICE_ADDRESS in result["data_schema"].schema

            # Select device
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF"}
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["data"][CONF_DEVICE_ADDRESS] == "AA:BB:CC:DD:EE:FF"
            assert result["data"][CONF_DEVICE_NAME] == "Test Device"
            assert result["data"][CONF_DEVICE_TYPE] == "crafty"

    async def test_scan_step_validation_device_lost(
        self, hass: HomeAssistant, mock_bluetooth_scanner, mock_device_info
    ):
        """Device listed then not found on re-scan during submit."""
        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            mock_device_info.address = "AA:BB:CC:DD:EE:FF"
            mock_device_info.name = "Test Device"
            mock_device_info.device_type = DeviceType.CRAFTY
            mock_scan.side_effect = [
                [mock_device_info],
                [],
            ]

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"setup_method": "scan"}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF"}
            )

            assert result["type"] == FlowResultType.FORM
            assert "Device not found" in result["errors"]["base"]

    async def test_manual_step_invalid_mac(
        self, hass: HomeAssistant, mock_bluetooth_scanner
    ):
        """Test manual step with invalid MAC address."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"setup_method": "manual"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "manual"

        # Enter invalid MAC
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE_ADDRESS: "invalid", CONF_DEVICE_NAME: "Test"},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"][CONF_DEVICE_ADDRESS] == "invalid_mac_address"

    async def test_manual_step_valid_mac(
        self, hass: HomeAssistant, mock_bluetooth_scanner, mock_device_info
    ):
        """Test manual step with valid MAC address."""
        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            mock_device_info.address = "AA:BB:CC:DD:EE:FF"
            mock_device_info.name = "Test Device"
            mock_device_info.device_type = DeviceType.VENTY
            mock_scan.return_value = [mock_device_info]

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"setup_method": "manual"}
            )

            # Enter valid MAC
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF",
                    CONF_DEVICE_NAME: "My Venty",
                },
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["data"][CONF_DEVICE_ADDRESS] == "AA:BB:CC:DD:EE:FF"
            assert result["data"][CONF_DEVICE_NAME] == "Test Device"  # From scan
            assert result["data"][CONF_DEVICE_TYPE] == "venty"

    async def test_manual_step_mac_not_found(
        self, hass: HomeAssistant, mock_bluetooth_scanner
    ):
        """Test manual step when MAC is not found in scan."""
        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = []

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"setup_method": "manual"}
            )

            # Enter MAC that's not found
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF",
                    CONF_DEVICE_NAME: "My Device",
                },
            )

            # Should still create entry even if not found
            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["data"][CONF_DEVICE_ADDRESS] == "AA:BB:CC:DD:EE:FF"
            assert result["data"][CONF_DEVICE_NAME] == "My Device"
            assert result["data"][CONF_DEVICE_TYPE] == "unknown"

    async def test_manual_step_scan_raises(
        self, hass: HomeAssistant, mock_bluetooth_scanner
    ):
        """Manual entry handles unexpected scan errors."""
        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            mock_scan.side_effect = RuntimeError("unexpected")

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"setup_method": "manual"}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {
                    CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF",
                    CONF_DEVICE_NAME: "Mine",
                },
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "manual"
            assert "base" in result["errors"]

    async def test_bluetooth_discovery(
        self, hass: HomeAssistant, mock_bluetooth_service_info, mock_device_info
    ):
        """Test Bluetooth discovery."""
        connected = AsyncMock()
        connected.update_state = AsyncMock()
        connected.state = MagicMock()
        connected.device_type = DeviceType.CRAFTY
        connected.name = "Test Device"
        connected.address = "AA:BB:CC:DD:EE:FF"

        with (
            patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan,
            patch.object(
                StorzBickelClient, "connect_device", new_callable=AsyncMock
            ) as mock_connect,
        ):
            mock_device_info.address = "AA:BB:CC:DD:EE:FF"
            mock_device_info.name = "Test Device"
            mock_device_info.device_type = DeviceType.CRAFTY
            mock_scan.return_value = [mock_device_info]
            mock_connect.return_value = connected

            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_BLUETOOTH},
                data=mock_bluetooth_service_info,
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "bluetooth_confirm"

            # Confirm → validate_input + create entry (no intermediate scan form)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {}
            )

            assert result["type"] == FlowResultType.CREATE_ENTRY
            assert result["data"][CONF_DEVICE_ADDRESS] == "AA:BB:CC:DD:EE:FF"
            assert result["data"][CONF_DEVICE_NAME] == "Test Device"
            assert result["data"][CONF_DEVICE_TYPE] == "crafty"

    async def test_bluetooth_discovery_not_supported(
        self, hass: HomeAssistant, mock_bluetooth_service_info
    ):
        """Test Bluetooth discovery for unsupported device."""
        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = []

            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_BLUETOOTH},
                data=mock_bluetooth_service_info,
            )

            assert result["type"] == FlowResultType.ABORT
            assert result["reason"] == "not_supported"

    async def test_duplicate_entry(
        self, hass: HomeAssistant, mock_bluetooth_scanner, mock_device_info
    ):
        """Test that duplicate entries are aborted."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test Device",
            unique_id="AA:BB:CC:DD:EE:FF",
            entry_id="test-entry-1",
            data={
                CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF",
                CONF_DEVICE_NAME: "Test Device",
                CONF_DEVICE_TYPE: "crafty",
            },
        )
        entry.add_to_hass(hass)

        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as mock_scan:
            mock_device_info.address = "AA:BB:CC:DD:EE:FF"
            mock_device_info.name = "Test Device"
            mock_device_info.device_type = DeviceType.CRAFTY
            mock_scan.return_value = [mock_device_info]

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {"setup_method": "scan"}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF"}
            )

            assert result["type"] == FlowResultType.ABORT
            assert result["reason"] == "already_configured"


class TestReconfigureFlow:
    """Reconfigure flow updates display name on the config entry."""

    async def test_reconfigure_updates_title(
        self, hass: HomeAssistant, mock_bluetooth_scanner
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Old label",
            data={
                CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF",
                CONF_DEVICE_NAME: "Old label",
                CONF_DEVICE_TYPE: "crafty",
            },
        )
        entry.add_to_hass(hass)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DEVICE_NAME: "New label"}
        )
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert entry.title == "New label"

    async def test_reconfigure_blank_name_keeps_mac_as_title(
        self, hass: HomeAssistant, mock_bluetooth_scanner
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Old",
            data={
                CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF",
                CONF_DEVICE_NAME: "Old",
                CONF_DEVICE_TYPE: "crafty",
            },
        )
        entry.add_to_hass(hass)
        flow = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_RECONFIGURE,
                "entry_id": entry.entry_id,
            },
        )
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], {CONF_DEVICE_NAME: "  "}
        )
        assert result["type"] == FlowResultType.ABORT
        assert entry.title == "AA:BB:CC:DD:EE:FF"


class TestValidateInput:
    """Tests for validate_input helper."""

    async def test_skip_scan(self, hass: HomeAssistant):
        """skip_scan returns normalized data without live BLE scan."""
        data = {
            CONF_DEVICE_ADDRESS: "aa:bb:cc:dd:ee:ff",
            CONF_DEVICE_NAME: "Mine",
        }
        out = await validate_input(hass, data, skip_scan=True)
        assert out[CONF_DEVICE_ADDRESS] == "AA:BB:CC:DD:EE:FF"
        assert out[CONF_DEVICE_NAME] == "Mine"

    async def test_scan_device_not_found(self, hass: HomeAssistant):
        with patch.object(StorzBickelClient, "scan", new_callable=AsyncMock) as scan:
            scan.return_value = []
            with pytest.raises(ValueError, match="Device not found"):
                await validate_input(
                    hass,
                    {CONF_DEVICE_ADDRESS: "AA:BB:CC:DD:EE:FF"},
                    skip_scan=False,
                )
