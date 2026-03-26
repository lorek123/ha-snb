# STORZ & BICKEL Web App Capability Audit

Date: 2026-03-26  
Frontend source: [https://app.storz-bickel.com/](https://app.storz-bickel.com/) (Web App `v3.4.1`)

## Local Snapshot

- A local snapshot was saved under `research/storz-bickel-app/`.
- Raw vendor assets are intentionally excluded from git via `.gitignore` (`research/storz-bickel-app/`).
- This keeps reverse-engineering artifacts local and out of GitHub while allowing reproducible analysis.

## Devices Supported By Frontend

From UI/device detection and handlers in the frontend JS (`main.js`, `crafty.js`, `qvap.js`, `volcano.js`, `workflow.js`), the app handles:

- `Crafty` / `Crafty+`
- `Venty`
- `Veazy`
- `Volcano` (Hybrid)

## Capability Matrix: Frontend vs Current Python Library

Legend:
- `Implemented`: present in current library API
- `Partial`: present indirectly/low-level or incomplete
- `Missing`: not currently implemented
- `Out of scope`: cloud/vendor endpoint or firmware transport not currently in library scope

| Device | Capability in frontend | Library status | Notes |
|---|---|---|---|
| Crafty/Crafty+ | Connect/disconnect, read serial/fw, live state notifications | Implemented | Present in `crafty.py` |
| Crafty/Crafty+ | Set target temp, heater on/off | Implemented | Present |
| Crafty/Crafty+ | Set boost temperature | Missing | Frontend writes dedicated boost char; no public API method in library |
| Crafty/Crafty+ | LED brightness, auto-shutoff, battery/charging | Implemented | Present |
| Crafty/Crafty+ | Vibration enable/disable | Implemented | Present |
| Crafty/Crafty+ | Permanent Bluetooth toggle | Missing | Frontend toggles project-status bit |
| Crafty/Crafty+ | Charge indicator lamp toggle | Missing | Frontend toggles project-status bit |
| Crafty/Crafty+ | Find My device | Implemented | `find_device()` exists |
| Crafty/Crafty+ | Device analysis flow | Missing | Frontend diagnostics flow not implemented |
| Crafty/Crafty+ | Firmware update flow | Out of scope | Frontend depends on vendor web endpoints/flow |
| Venty | Connect/disconnect, fw/sn/status polling | Implemented | Present in `venty.py` |
| Venty | Set target temp, heater mode, boost, superboost | Implemented | Present |
| Venty | Temp unit, eco charge, eco voltage, boost visualization | Implemented | Present |
| Venty | Brightness (1-9) | Missing | Frontend supports via cmd `0x06` |
| Venty | Vibration toggle | Missing | Frontend supports via cmd `0x06` |
| Venty | Boost/Superboost timeout setting | Missing | Frontend supports via cmd `0x06` bit |
| Venty | Find My device | Implemented | `find_device()` exists |
| Venty | Factory reset | Missing | Frontend supports via settings flag |
| Venty | Analysis flow | Missing | Frontend supports local+upload analysis |
| Venty | Firmware update (bootloader/app) | Out of scope | Frontend uses vendor endpoints and bootloader protocol |
| Veazy | All qvap controls (target/boost/superboost/heater/settings/find/analysis/update) | Missing | No `Veazy` device type/class in current library |
| Volcano Hybrid | Connect/disconnect, serial/fw, notifications | Implemented | Present in `volcano.py` |
| Volcano Hybrid | Set target temp, heater, pump | Implemented | Present |
| Volcano Hybrid | Brightness, auto-shutoff | Implemented | Present |
| Volcano Hybrid | Temp unit/display-on-cooling/vibration flags | Partial | Supported via status register setters (raw-ish API) |
| Volcano Hybrid | Workflow execution (Balloon/Flow 1/2/3) | Missing | Frontend orchestrates timed heat+pump sequences |
| Volcano Hybrid | Device analysis flow | Missing | Frontend reads history/error registers and reports |
| Volcano Hybrid | Firmware update flow | Out of scope | Frontend uses dedicated hybrid firmware endpoint + bootloader transport |

## Key Gaps vs Current Repo Claims

- Frontend supports `Veazy`, but library currently models only `VOLCANO`, `VENTY`, `CRAFTY` in `DeviceType`.
- README currently describes support as "comprehensive/all features", but frontend shows additional feature surface not yet exposed in library API (brightness/vibration for qvap devices, analysis flows, workflow orchestration, extra settings toggles).

## Home Assistant Integration Priorities

Recommended order for highest HA value and lowest risk:

1. **High priority entities/services**
   - Add `Veazy` discovery/type support (if protocol parity with qvap path is confirmed).
   - Add qvap `brightness`, `vibration`, and `boost timeout` controls.
   - Add Crafty `boost temperature` setter.
2. **Medium priority**
   - Add explicit helpers for Volcano display/vibration/temp-unit bits (currently available through raw register writes).
   - Add optional service wrappers for "Find My" and factory reset (with safeguards).
3. **Lower priority / caution**
   - Workflow presets for Volcano (service-level orchestration in HA).
   - Analysis and firmware-update features only if explicitly scoped; likely separate module due to risk.

## Suggested Next Implementation Slices

- Slice 1: Add missing qvap settings APIs (brightness/vibration/boost-timeout) + tests.
- Slice 2: Add Crafty boost temperature setter + tests.
- Slice 3: Add Veazy type + connect/discovery mapping + baseline tests.
- Slice 4: Add friendly Volcano settings helpers and optional workflow service abstraction.

## Source Artifacts Used

- Live app: [https://app.storz-bickel.com/](https://app.storz-bickel.com/)
- Local snapshot:
  - `research/storz-bickel-app/index.html`
  - `research/storz-bickel-app/js/main.js`
  - `research/storz-bickel-app/js/crafty.js`
  - `research/storz-bickel-app/js/qvap.js`
  - `research/storz-bickel-app/js/volcano.js`
  - `research/storz-bickel-app/js/workflow.js`
- Library sources:
  - `src/storzandbickel_ble/crafty.py`
  - `src/storzandbickel_ble/venty.py`
  - `src/storzandbickel_ble/volcano.py`
  - `src/storzandbickel_ble/models.py`
  - `README.md`
