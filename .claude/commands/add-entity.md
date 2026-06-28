---
description: Add a new entity/feature following this repo's conventions
argument-hint: <what to add, e.g. "auto-shutoff timer number for Venty">
---

Implement: **$1**

Follow the existing patterns exactly — study a sibling platform file first (e.g. `number.py`,
`switch.py`) before writing anything.

Checklist:
1. Read `coordinator.py` to confirm the underlying data/command already exists (or add it there,
   respecting the GATT-error-swallowing workarounds and backoff logic).
2. Subclass `StorzBickelEntity`; read state from `self.coordinator.data`, never block on BLE
   directly in the entity.
3. Put any new constants in `const.py`. Route device-type checks through `device_type_slug()`.
4. Gate the feature to the devices that actually support it (see the support matrix in `README.md`).
5. Add user-visible strings to `translations/en.json`.
6. Add/extend the matching `tests/test_*.py` so coverage stays ≥ 95%.
7. Update `README.md`'s entity list and support matrix if the surface changed.
8. Run `/check` and make it green before declaring done.
