# Storz & Bickel Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Home Assistant integration for controlling Storz & Bickel vaporizers (Volcano Hybrid, Venty, Veazy, and Crafty/Crafty+) via Bluetooth Low Energy (BLE).

## Features

- **Full Device Support**: Control Volcano Hybrid, Venty, Veazy, and Crafty/Crafty+ devices (one Bluetooth device per config entry)
- **Climate Control**: Set target temperature and control heater
- **Temperature Monitoring**: Real-time current temperature sensor
- **Battery Monitoring**: Battery level sensor for portable devices (Crafty/Crafty+, Venty)
- **Air Pump Control**: Switch for Volcano Hybrid air pump
- **Boost Mode**: Button to activate boost mode on supported devices
- **Auto-Discovery**: Automatic device discovery via Bluetooth

## Supported Devices

| Device         | Temperature Control | Heater Control | Battery | Air Pump | Boost Mode |
| -------------- | ------------------- | -------------- | ------- | -------- | ---------- |
| Volcano Hybrid | ✅                   | ✅              | ❌       | ✅        | ❌          |
| Venty          | ✅                   | ✅              | ✅       | ❌        | ✅          |
| Crafty/Crafty+ | ✅                   | ✅              | ✅       | ❌        | ✅          |

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to Integrations
3. Click the three dots menu (⋮) in the top right
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/lorek123/ha-snb`
6. Select category: "Integration"
7. Click "Add"
8. Search for "Storz & Bickel" in HACS
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/storzandbickel` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services → Add Integration

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Storz & Bickel**
4. The integration will scan for available devices
5. Select your device from the list
6. The device will be automatically configured

### Bluetooth Requirements

- A Bluetooth adapter with BLE support
- Bluetooth must be enabled in Home Assistant
- The device must be powered on and in range

## Entities

After setup, the following entities will be created:

### Climate Entity
- **Temperature Control**: Set target temperature (40-230°C)
- **Heater Control**: Turn heater on/off
- **Current Temperature**: Real-time temperature reading

### Sensor Entities
- **Current Temperature**: Current device temperature
- **Battery Level**: Battery percentage (Crafty/Crafty+, Venty only)

### Switch Entities
- **Air Pump**: Control air pump (Volcano Hybrid only)

### Button Entities
- **Boost Mode**: Activate boost mode (Crafty/Crafty+, Venty, Veazy)

### Number Entities
- **Brightness** (1–9): Venty, Veazy
- **Boost temperature**: Crafty/Crafty+

### Select Entities
- **Workflow preset**: Volcano Hybrid (runs device workflow preset)

### Switch Entities (besides air pump)
- **Vibration**, **Boost timeout disabled**: Venty, Veazy

## Removal

1. Open **Settings** → **Devices & services**.
2. Open the **Storz & Bickel** integration card.
3. Use the three-dot menu on the device entry and choose **Delete** (or remove the integration and confirm).

Restart Home Assistant if you also removed the custom component files manually.

## Usage Examples

### Setting Temperature

```yaml
# Example automation
automation:
  - alias: "Set Venty to 190°C"
    trigger:
      - platform: state
        entity_id: input_boolean.venty_session
        to: "on"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.venty_temperature
        data:
          temperature: 190
      - service: climate.set_hvac_mode
        target:
          entity_id: climate.venty_temperature
        data:
          hvac_mode: heat
```

### Monitoring Temperature

```yaml
# Example sensor template
sensor:
  - platform: template
    sensors:
      venty_temp:
        friendly_name: "Venty Temperature"
        value_template: "{{ states('sensor.venty_current_temperature') }}°C"
```

## Example dashboard (Lovelace)

Ready-made cards are in [`examples/lovelace-storzandbickel.yaml`](examples/lovelace-storzandbickel.yaml): a full **masonry** view with a **thermostat** card, entity groups for status and controls, and a small **button** row for heat / off / boost. Replace the placeholder prefix (`my_device`) with your real entity slug from **Developer tools → States**, and delete rows for entities your hardware does not provide (e.g. no battery on Volcano, no brightness on Crafty).

## Troubleshooting

### Device Not Found

- Ensure Bluetooth is enabled in Home Assistant
- Make sure the device is powered on and in range
- Try restarting Home Assistant
- Check that the device is not connected to another app

### Connection Issues

- Ensure the device is within Bluetooth range
- Try disconnecting from other apps (official Storz & Bickel app)
- Restart the device
- Check Home Assistant logs for errors

### Temperature Not Updating

- The integration polls the device every 5 seconds
- If updates stop, try restarting the integration
- Check device battery level (for portable devices)

## Development

This integration uses the [storzandbickel-ble](https://pypi.org/project/storzandbickel-ble/) Python library.

### Running Tests

Install test dependencies:

```bash
pip install -e ".[test]"
```

Run tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=custom_components/storzandbickel --cov-report=html
```

### Test Structure

- `tests/test_config_flow.py` - Configuration flow tests
- `tests/test_coordinator.py` - Data coordinator tests
- `tests/test_climate.py` - Climate entity tests
- `tests/test_sensor.py` - Sensor entity tests
- `tests/test_switch.py` - Switch entity tests
- `tests/test_button.py` - Button entity tests
- `tests/test_integration.py` - Integration setup/teardown tests

### Quality scale / typing notes

This repo targets common [Home Assistant integration quality scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/checklist) practices where they apply to a **HACS** integration. Core-only items (e.g. official branding repo) may not apply. **Inject websession** is not relevant (no HTTP client integration dependency). Strict typing is enforced incrementally via `pyright` (see `pyproject.toml`).

## Disclaimer

This integration is based on reverse engineering and is not officially supported by Storz & Bickel. Use at your own risk. The authors are not responsible for any damage to devices.

## License

MIT License

## Support

For issues, feature requests, or contributions, please visit the [GitHub repository](https://github.com/lorek123/ha-snb).
