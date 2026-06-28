---
name: analyze-sb-app
description: >-
  Map Storz & Bickel app / BLE-library capabilities onto this Home Assistant
  integration's entity surface, and run gap analysis between what the official
  app (and the storzandbickel-ble library) can do versus what we expose as HA
  entities. Use this whenever the task is "what app feature is missing from the
  HA integration", "should this be a number/switch/select/sensor", "wire up the
  new library method as an entity", "audit the integration against the app", or
  deciding which device types get a given control. It reads the library's
  capability matrix (docs/app-frontend-capabilities.md) and protocol notes
  (s&b_procol.md) in the sibling storzandbickel-ble checkout as the source of
  truth, then plans the HA entity work. Trigger even when the user just names a
  feature ("expose Venty brightness", "add Crafty boost temp to HA") or asks why
  a control isn't showing up for a device.
---

# Map the S&B app's capabilities to HA entities

This repo is the **HA glue**: it does not talk BLE directly. Every control here is a
thin entity over a method/state the `storzandbickel-ble` library already provides,
which in turn came from reverse-engineering the official app. So "analysing the app
for HACS" means two related jobs:

1. **Gap analysis** — what can the app (and the library) do that we don't surface yet?
2. **Mapping** — given a confirmed library capability, what HA entity is it, on which
   platform, gated to which devices?

The actual app reverse-engineering happens in the **library repo** — it owns the app
snapshot and the protocol. This skill consumes its conclusions; don't re-decompile JS
here.

## Source of truth (the sibling library checkout)

The library repo is a sibling checkout (in this environment:
`/home/lorek/storzandbickel-ble`; otherwise look for `../storzandbickel-ble` or ask).
Read these — they're already a digested view of the app:

- `docs/app-frontend-capabilities.md` — **the capability matrix**: every app feature
  with a status of Implemented / Partial / Missing / Out of scope, plus a
  HA-prioritized "next slices" list. This is your primary input for gap analysis.
- `s&b_procol.md` — protocol reference (UUIDs, command bytes, status-register bits) if
  you need to understand what a capability actually does.
- `src/storzandbickel_ble/{crafty,venty,volcano}.py` and `models.py` — the **public
  API**: which `set_*()` / `async` methods and `*State` fields actually exist. An HA
  entity can only expose what's here. If the capability matrix says "Missing" at the
  library level, the library work must land first — say so rather than stubbing it.

If the sibling checkout isn't present, tell the user you need it (or the relevant
files pasted) — guessing at the library API is how these entities break.

## How a capability becomes an entity

The data path is always the same; follow `coordinator.py` first, then the sibling
platform file closest to what you're adding.

```
library:  device.set_<feature>(value)         # the action
          <Device>State.<field>               # the readback
   │
coordinator.py:  polls device → coordinator.data = {"device_type", "state": <DeviceState>, "device": <BaseDevice>}
   │
entity (number/switch/select/sensor/...):
   read:    self.coordinator.data["state"].<field>
   write:   await self.coordinator.device.set_<feature>(value)
```

Existing entities follow this exactly — e.g. `number.py`'s `BrightnessNumber` reads
`state.brightness` and calls `device.set_brightness(int(value))`, guarding on
`hasattr(self.coordinator.device, "set_brightness")` so a device without the method
just doesn't get the entity.

### Picking the platform

Map the capability's shape to the HA platform, matching what's already in the repo:

- **number.py** — a bounded numeric setpoint (target/boost temperature, LED
  brightness 1–9, auto-shutoff minutes).
- **switch.py** — a boolean toggle (vibration, eco-charge, a status-register flag).
- **select.py** — a small enumerated choice (heater mode, temperature unit).
- **sensor.py** / **binary_sensor.py** — read-only state (current temp, battery,
  charging, heating/ready).
- **button.py** — a momentary action (find-my-device, factory reset — guard
  destructive ones).
- **climate.py** — only the unified heater/temperature surface; most features are
  better as their own entity than crammed in here.

## Device gating — the thing that's easy to get wrong

Features are per-device (see the support matrix in `README.md` and the library's
capability matrix). A Venty has a battery; a Volcano has a pump; Crafty boost temp is
Crafty-only. Gate entities so they only appear where supported:

- Normalize the device type through `const.device_type_slug()` — never compare
  `.name`/`.value` directly, because `DeviceType` representation varies across library
  versions.
- Belt-and-suspenders: also guard on `hasattr(self.coordinator.device, "set_<x>")` so a
  capability missing on a given firmware/library degrades to "no entity" instead of an
  AttributeError at runtime.

## Output: a gap-analysis / mapping plan

When auditing or planning, produce this so the user can act:

```
## <feature> — <device(s)>
- Library API: device.set_<x>() / state.<field>   (Present | MISSING — needs library work first)
- App reference: app-frontend-capabilities.md row "<...>"  (s&b_procol.md if protocol detail matters)
- HA platform: number | switch | select | sensor | button | climate
- Entity: <proposed name/key>, range/options <...>, unit <...>
- Device gating: <slugs via device_type_slug()> + hasattr guard
- New strings: translations/en.json key(s)
- README: support-matrix / entity-list row to add
- Priority: <high/med/low, mirroring the library's prioritization>
```

For a full audit, walk every "Missing" / "Partial" row in the library's capability
matrix, decide whether it's an HA entity (some are out of scope — firmware, cloud
analysis), and emit one block each, ordered highest-HA-value-lowest-risk first.

## Handing off to implementation

This skill plans; it doesn't have to build. When a mapping is agreed and the library
API exists, run **`/add-entity`** — that command already encodes the implementation
checklist (subclass `StorzBickelEntity`, constants in `const.py`, gate by device,
add `translations/en.json` strings, extend `tests/test_*.py` for the ≥95% coverage
gate, update `README.md`) and finishes with `/check`.

If the capability is **Missing at the library level**, the work belongs in the
`storzandbickel-ble` repo first (its own `analyze-sb-app` skill covers extracting the
protocol from the app) — flag that dependency instead of faking the entity here.
