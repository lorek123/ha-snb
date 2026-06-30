# Storz & Bickel Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Home Assistant integration for controlling Storz & Bickel vaporizers (Volcano Hybrid, Venty, Veazy, and Crafty/Crafty+) via Bluetooth Low Energy (BLE).

## Features

- **All devices**: Volcano Hybrid, Venty, Veazy, and Crafty/Crafty+ (one Bluetooth device per config entry), with automatic Bluetooth discovery.
- **Climate control**: target temperature, heater on/off, and real-time current-temperature reporting.
- **Full settings surface**: LED/display brightness, auto-off timers, vibration, boost/superboost offsets, ECO charging modes, display-on-cooling, charge-LED and permanent-Bluetooth, and more — exposed as numbers, switches, and selects per device.
- **Volcano workflows**: built-in presets (balloon / flow 1–3) **plus a custom workflow action** for your own timed heat-and-pump sequences.
- **Diagnostics action**: on-demand `run_analysis` that returns device status, detected error flags, and raw registers as action **response data**.
- **Status sensors**: temperature, battery, charging, "ready" (at-temperature), usage time, connection state, and signal strength.
- **Recovery tools**: reconnect/refresh buttons plus connection backoff, so a device that's off or out of range doesn't spam the Bluetooth proxy.

## Supported Devices

| Device         | Climate | Battery | Charging sensor | Air pump | Boost / Superboost      | Workflows          | Diagnostics |
| -------------- | :-----: | :-----: | :-------------: | :------: | ----------------------- | ------------------ | :---------: |
| Volcano Hybrid | ✅       | —       | —               | ✅        | —                       | ✅ presets + custom | ✅           |
| Venty          | ✅       | ✅       | ✅               | —        | ✅ offsets + heater mode | —                  | ✅           |
| Veazy          | ✅       | ✅       | ✅               | —        | ✅ offsets + heater mode | —                  | ✅           |
| Crafty/Crafty+ | ✅       | ✅       | — (LED only)    | —        | ✅ boost button          | —                  | ✅           |

Entity availability is per-device — see **Entities** below for the full list.

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

After setup the following entities are created. Availability is per-device — the applicable device(s) are shown in parentheses.

### Climate
- **Temperature / heater** — set target temperature and turn the heater on/off (all).

### Sensors
- **Current temperature** (all)
- **Battery level** (Crafty/Crafty+, Venty, Veazy)
- **Usage / heating time** (Crafty/Crafty+, Volcano)
- **Connection state** — `connected` / `disconnected` (all, diagnostic)
- **Signal strength** — BLE RSSI when provided (all, diagnostic)

### Binary sensors
- **Charging** (Venty, Veazy)
- **Ready** — setpoint reached / at temperature (Crafty/Crafty+, Venty, Veazy)

### Numbers
- **Brightness** 1–9 (Venty, Veazy)
- **Boost offset**, **Superboost offset** — degrees above base (Venty, Veazy)
- **Boost temperature** (Crafty/Crafty+)
- **LED brightness** — 0–100 (Crafty/Crafty+), 1–9 (Volcano)
- **Auto-off time** (Crafty/Crafty+, Volcano)

### Switches
- **Air pump** (Volcano)
- **Vibration** (Crafty/Crafty+, Venty, Veazy)
- **Superboost** (Crafty/Crafty+)
- **Charge LED**, **Permanent Bluetooth** (Crafty/Crafty+)
- **Boost timeout disabled**, **ECO charge optimization**, **ECO charge limit** (Venty, Veazy)
- **Boost visualization** (Venty)
- **Display on cooling**, **Vibration on ready** (Volcano)

### Selects
- **Heater mode** — normal / boost / superboost (Venty, Veazy)
- **Workflow preset** — balloon / flow 1–3 (Volcano)

### Buttons
- **Reconnect**, **Refresh** (all)
- **Find device** (Crafty/Crafty+, Venty, Veazy)
- **Boost mode** (Crafty/Crafty+)

## Actions

### `storzandbickel.run_analysis`

Runs the device's on-board diagnostics and **returns a report** (overall status, heuristic warnings, detected error flags, and raw register/history values) as action response data. Per-bit error *meanings* are decoded by Storz & Bickel's servers, so the report flags **which** error bits are set rather than naming each cause.

```yaml
action: storzandbickel.run_analysis
target:
  entity_id: climate.my_device_temperature
response_variable: report
```

### `storzandbickel.run_workflow` (Volcano)

Runs a **custom Volcano workflow** — a sequence of timed heat-and-pump steps. Each step sets a temperature, optionally waits for it, holds for `hold_seconds`, then runs the pump for `pump_seconds`. Blocks until the sequence finishes (watch the climate and air-pump entities for progress). For the four built-in presets, use the **Workflow preset** select instead.

```yaml
action: storzandbickel.run_workflow
target:
  entity_id: climate.my_volcano_temperature
data:
  steps:
    - temperature: 185
      hold_seconds: 10
      pump_seconds: 8
    - temperature: 200
      pump_seconds: 12
```

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

### Volcano workflow (entity-only automation)

For most cases the `storzandbickel.run_workflow` action (see **Actions** above) is simpler. If you'd rather orchestrate it yourself with the raw entities — e.g. to add conditions or notifications — this works too:

```yaml
script:
  volcano_fill_bag:
    alias: "Volcano fill bag"
    sequence:
      - action: climate.set_hvac_mode
        target:
          entity_id: climate.my_device_temperature
        data:
          hvac_mode: heat
      - wait_template: >
          {{ state_attr('climate.my_device_temperature', 'current_temperature') | float(0)
             >= state_attr('climate.my_device_temperature', 'temperature') | float(0) }}
        timeout: "00:10:00"
        continue_on_timeout: true
      - action: switch.turn_on
        target:
          entity_id: switch.my_device_air_pump
      - delay: "00:00:40"
      - action: switch.turn_off
        target:
          entity_id: switch.my_device_air_pump
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

Use **uv** so dependencies match CI and Home Assistant can resolve `custom_components` from the repo (avoid `pip install -e .`, which can break loader discovery on Python 3.14+ setuptools editables):

```bash
uv sync --extra test --extra dev --no-install-project
PYTHONPATH=. uv run pytest
```

Coverage (same as CI):

```bash
PYTHONPATH=. uv run pytest --cov=custom_components/storzandbickel --cov-report=html
```

PySerial is not used: HA’s `usb` import path is satisfied in tests by the `serial.*` stubs in `tests/conftest.py`.

Typecheck (CI runs this after install):

```bash
uv run pyright custom_components/storzandbickel
```

### Test Structure

- `tests/test_config_flow.py` — configuration flow
- `tests/test_coordinator.py` — data coordinator (connect/poll/backoff)
- `tests/test_climate.py` — climate entity + `run_analysis` / `run_workflow` actions
- `tests/test_sensor.py`, `tests/test_binary_sensor.py` — sensors
- `tests/test_number.py`, `tests/test_switch.py`, `tests/test_select.py`, `tests/test_button.py` — controls
- `tests/test_platform_setup.py` — per-device entity gating
- `tests/test_diagnostics.py`, `tests/test_const.py` — diagnostics + helpers
- `tests/test_integration.py` — integration setup/teardown

### Quality scale / typing notes

This repo targets common [Home Assistant integration quality scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/checklist) practices where they apply to a **HACS** integration. Core-only items (e.g. official branding repo) may not apply. **Inject websession** is not relevant (no HTTP client integration dependency). Strict typing is checked with `pyright` in CI and via the `dev` dependency group in `pyproject.toml`.

## Disclaimer

This integration is based on reverse engineering and is not officially supported by Storz & Bickel. Use at your own risk. The authors are not responsible for any damage to devices.

## License

MIT License

## Support

For issues, feature requests, or contributions, please visit the [GitHub repository](https://github.com/lorek123/ha-snb).
