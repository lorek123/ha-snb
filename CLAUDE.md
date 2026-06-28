# CLAUDE.md

Guidance for Claude Code (and other agents) working in this repo. Read this before editing.

## What this is

A **HACS custom integration** for Home Assistant that controls Storz & Bickel vaporizers
(Volcano Hybrid, Venty, Veazy, Crafty/Crafty+) over Bluetooth LE. Domain: `storzandbickel`.
All BLE protocol logic lives in the external `storzandbickel-ble` PyPI library — this repo is
the HA glue (config flow, coordinator, entities). It is `local_polling`, one device per config entry.

## Environment & commands

Python **3.14+**, managed with **uv**. Use these exact commands — they match CI.

```bash
# One-time / after dependency changes
uv sync --extra test --extra dev --no-install-project

# Tests (PYTHONPATH=. is REQUIRED — see gotchas)
PYTHONPATH=. uv run pytest

# Coverage (CI parity, must stay >= 95%)
PYTHONPATH=. uv run pytest --cov=custom_components/storzandbickel --cov-report=term-missing

# Type check (CI runs this, basic mode)
uv run pyright custom_components/storzandbickel

# Lint / format (ruff is a dev dep; run it before finishing — see "Definition of done")
uv run ruff format custom_components tests
uv run ruff check --fix custom_components tests
```

## Critical gotchas (these will waste your time if ignored)

- **Never `pip install -e .`** Editable installs register `custom_components` on a setuptools
  path hook that is not a real directory, which breaks `homeassistant.loader`'s
  `Path(custom_components.__path__).iterdir()` on Python 3.14+. Always use
  `uv sync ... --no-install-project` and run pytest with `PYTHONPATH=.`.
- **`PYTHONPATH=.` is mandatory for pytest** so HA can resolve `custom_components` from the repo root.
- **PySerial is not a dependency.** HA's `usb` import path is satisfied in tests by the `serial.*`
  stubs in `tests/conftest.py`. Don't add pyserial; don't delete those stubs.
- **The `storzandbickel-ble` library swallows most GATT errors.** Crafty/Volcano `update_state()`
  can return without raising even on a failed poll, leaving stale state with `last_update_success`
  still `True`. The coordinator works around this with explicit timeouts
  (`UPDATE_STATE_TIMEOUT`, `LIVE_BLE_VERIFY_TIMEOUT`) and connection backoff. Preserve that logic;
  don't "simplify" it away.
- **`DeviceType` spans library versions.** `const.device_type_slug()` normalizes IntEnum (>=0.1.4),
  older string enums, and `"DeviceType.VENTY"` reprs. Route all device-type → slug conversion
  through it rather than calling `.name`/`.value` directly.

## Architecture map

```
custom_components/storzandbickel/
  __init__.py        # setup_entry / unload_entry, platform forwarding
  coordinator.py     # HEART: BLE connect/poll, timeouts, backoff, state dict  <- read this first
  entity.py          # StorzBickelEntity base (CoordinatorEntity), dynamic device_info
  config_flow.py     # Bluetooth discovery + manual setup (largest file)
  const.py           # DOMAIN, conf keys, device-type slugs, device_type_slug()
  data.py            # typed runtime data container
  climate / sensor / binary_sensor / switch / number / select / button / diagnostics .py
  manifest.json      # HA manifest — runtime requirement pin lives here
tests/               # one test_*.py per platform, conftest.py has fixtures + serial stubs
```

Data flows: `coordinator` polls the device → builds a state dict → entities read
`self.coordinator.data`. New entities subclass `StorzBickelEntity` and set `_attr_has_entity_name`.

## Conventions

- Every module starts with `"""docstring."""` then `from __future__ import annotations`.
- Constants go in `const.py`; no magic strings for conf keys or attributes.
- Entities are coordinator-driven; never do blocking BLE calls directly in an entity.
- New user-visible strings need an entry in `translations/en.json`.
- Match existing logging style (`_LOGGER = logging.getLogger(__name__)`).

## Version-sync invariant

The library requirement appears in **two** places that MUST agree:
- `custom_components/storzandbickel/manifest.json` → `requirements` (what HA installs at runtime — source of truth)
- `pyproject.toml` → `dependencies` (the dev/test env)

And the integration version appears in **both** `manifest.json` `version` and `pyproject.toml` `version`.
When bumping either, update all of them in the same change. (See `/release`.)

## Definition of done

Before declaring any change complete, all three must pass locally:

1. `uv run ruff check custom_components tests` (clean)
2. `uv run pyright custom_components/storzandbickel` (no new errors — basic mode)
3. `PYTHONPATH=. uv run pytest` (green, coverage ≥ 95%)

If you add a code path, add/extend the matching `tests/test_*.py` — the 95% gate is enforced in CI
and will fail the PR otherwise. Run `/check` to do all three in one step.

## Releasing

Use `/release`. It bumps the version in both `manifest.json` and `pyproject.toml`, reminds you to
align the library pin, and tags. CI builds the HACS zip on tag push.

## Safety notes for agents

- This integration ships to real Home Assistant users; treat correctness around BLE
  connect/disconnect and the coordinator's error handling as load-bearing.
- Don't commit or push without explicit confirmation (enforced by `.claude/settings.json`).
- Secrets/`.env`/`*.pem` reads are denied by policy — you don't need them here.
