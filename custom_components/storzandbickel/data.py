"""Runtime data attached to the config entry."""

from __future__ import annotations

from dataclasses import dataclass

from .coordinator import StorzBickelDataUpdateCoordinator


@dataclass
class StorzBickelRuntimeData:
    """Hold integration runtime objects for ConfigEntry.runtime_data."""

    coordinator: StorzBickelDataUpdateCoordinator
