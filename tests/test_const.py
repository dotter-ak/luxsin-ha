"""Unit tests for model detection and per-model input lists
(custom_components/luxsin/const.py).
"""
from __future__ import annotations

import sys

# conftest.py loads const.py directly by file path (bypassing
# custom_components/luxsin/__init__.py, which imports homeassistant) and
# registers it under this name.
_const = sys.modules["luxsin_const"]


def test_normalize_model_key_x8() -> None:
    assert _const.normalize_model_key("Luxsin-X8") == "x8"


def test_normalize_model_key_x9() -> None:
    assert _const.normalize_model_key("Luxsin-X9") == "x9"


def test_normalize_model_key_case_insensitive() -> None:
    assert _const.normalize_model_key("luxsin-x9") == "x9"
    assert _const.normalize_model_key("LUXSIN-X8") == "x8"


def test_normalize_model_key_unknown_falls_back_to_default() -> None:
    assert _const.normalize_model_key("SomeOtherDevice") == _const.DEFAULT_MODEL_KEY
    assert _const.normalize_model_key(None) == _const.DEFAULT_MODEL_KEY
    assert _const.normalize_model_key("") == _const.DEFAULT_MODEL_KEY


def test_input_names_for_x8() -> None:
    names = _const.input_names_for("x8")
    assert names == ["USB", "USB-C", "Coaxial", "Optical", "Bluetooth", "IIS"]
    assert len(names) == 6


def test_input_names_for_x9() -> None:
    names = _const.input_names_for("x9")
    assert names == [
        "USB-B",
        "USB-C",
        "Coaxial",
        "Optical",
        "Bluetooth",
        "HDMI-EARC",
        "Audio-in",
        "Local",
    ]
    assert len(names) == 8


def test_input_names_for_unknown_model_falls_back() -> None:
    """An unrecognized model key should fall back to DEFAULT_MODEL_KEY's
    list rather than raising, so a future/unrecognized "device" string
    doesn't break the media_player/select entities."""
    assert _const.input_names_for("some_future_model") == _const.input_names_for(
        _const.DEFAULT_MODEL_KEY
    )


def test_output_names_shared_across_models() -> None:
    """Output names are confirmed identical for X8 and X9 in the official
    docs, so there's a single shared list rather than a per-model table."""
    assert _const.OUTPUT_NAMES == ["XLR", "RCA", "Headphone", "XLR + RCA"]


def test_x8_and_x9_input_lists_differ() -> None:
    """Regression guard: if someone "simplifies" this back to one shared
    list, this test should fail loudly."""
    assert _const.input_names_for("x8") != _const.input_names_for("x9")


def test_crossfeed_options_are_model_specific() -> None:
    assert _const.crossfeed_names_for("x8") == _const.CROSSFEED_NAMES
    assert _const.crossfeed_names_for("x9") == [*_const.CROSSFEED_NAMES, "Custom"]


def test_normalize_device_id() -> None:
    assert _const.normalize_device_id("AA:BB:CC:DD:EE:FF") == "aabbccddeeff"
    assert _const.normalize_device_id("aa-bb-cc-dd-ee-ff") == "aabbccddeeff"
    assert _const.normalize_device_id(None) is None
    assert _const.normalize_device_id("not-a-mac") is None
