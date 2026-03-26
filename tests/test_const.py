"""Tests for const helpers."""
from __future__ import annotations

from storzandbickel_ble.models import DeviceType

from custom_components.storzandbickel.const import device_type_slug


def test_device_type_slug_none():
    assert device_type_slug(None) is None


def test_device_type_slug_int_enum():
    assert device_type_slug(DeviceType.VENTY) == "venty"
    assert device_type_slug(DeviceType.VEAZY) == "veazy"


def test_device_type_slug_string_value():
    class Legacy:
        value = "crafty"

    assert device_type_slug(Legacy()) == "crafty"


def test_device_type_slug_dotted_repr_string():
    assert device_type_slug("DeviceType.VOLCANO") == "volcano"


def test_device_type_slug_plain_string_lowercase():
    assert device_type_slug("VENTY") == "venty"
