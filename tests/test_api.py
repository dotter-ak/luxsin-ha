"""Unit tests for the Luxsin X8 wire protocol codec (custom_components/luxsin/api.py).

Covers:
  - Synthetic round-trip: encode a payload the way the device does
    (JSON -> base64 -> custom alphabet -> gzip), decode it with our
    client, and check we get the original JSON back - including the
    "zero value" edge case that historically breaks naive JSON-presence
    checks (e.g. ArduinoJson's `if (root["field"])` truthiness bug this
    project's ESPHome predecessor hit).
  - Regression fixtures: real /dev/info.cgi?action=sync and
    ?action=syncPeq captures from a live Luxsin X8, hex-dumped and
    pasted directly from a browser devtools Network tab (so they arrive
    here already gunzipped, exercising the "no gzip magic bytes" branch
    of _decode_payload).
"""
from __future__ import annotations

import base64
import gzip
import json
import random
import sys

import pytest

# conftest.py loads api.py directly by file path (bypassing
# custom_components/luxsin/__init__.py, which imports homeassistant) and
# registers it under this name.
_api = sys.modules["luxsin_api"]
LuxsinProtocolError = _api.LuxsinProtocolError
_CUSTOM_ALPHABET = _api._CUSTOM_ALPHABET
_STANDARD_ALPHABET = _api._STANDARD_ALPHABET
_decode_payload = _api._decode_payload

_ENCODE_TABLE = str.maketrans(_STANDARD_ALPHABET, _CUSTOM_ALPHABET)


def _encode_like_device(payload: dict) -> bytes:
    """Reverse of _decode_payload: JSON -> base64 -> custom alphabet -> gzip."""
    json_bytes = json.dumps(payload).encode()
    std_b64 = base64.b64encode(json_bytes).decode()
    custom_b64 = std_b64.translate(_ENCODE_TABLE)
    return gzip.compress(custom_b64.encode())


@pytest.mark.parametrize("trial", range(50))
def test_round_trip_random_payloads(trial: int) -> None:
    """Random payloads survive encode -> decode unchanged."""
    rng = random.Random(trial)
    payload = {
        "volume": rng.randint(0, 200),
        "input": rng.randint(0, 7),
        "output": rng.randint(0, 3),
        "extra_field": rng.choice([0, 1, "", "text", None, True, False]),
    }
    wire = _encode_like_device(payload)
    assert _decode_payload(wire) == payload


def test_round_trip_zero_values() -> None:
    """Zero is a valid, meaningful value for volume/input/output - this is
    exactly the case ArduinoJson's truthiness check got wrong upstream in
    the ESPHome version of this project (`if (root["field"])` is False
    when the field is 0). The Python client uses `.get()` so this isn't a
    risk here, but it's worth pinning as a regression test."""
    payload = {"volume": 0, "input": 0, "output": 0}
    wire = _encode_like_device(payload)
    decoded = _decode_payload(wire)
    assert decoded == payload
    assert decoded["volume"] == 0
    assert decoded["input"] == 0
    assert decoded["output"] == 0


def test_decode_rejects_non_json_object() -> None:
    """A validly-encoded JSON array (not object) should raise, not silently
    return something callers would misuse as a dict."""
    json_bytes = json.dumps([1, 2, 3]).encode()
    std_b64 = base64.b64encode(json_bytes).decode()
    custom_b64 = std_b64.translate(_ENCODE_TABLE)
    wire = gzip.compress(custom_b64.encode())
    with pytest.raises(LuxsinProtocolError):
        _decode_payload(wire)


def test_decode_rejects_garbage() -> None:
    with pytest.raises(LuxsinProtocolError):
        _decode_payload(b"not a valid payload at all")


def test_decode_handles_missing_base64_padding() -> None:
    """Real device responses have been observed without full Base64
    padding; _decode_payload should restore it rather than fail."""
    payload = {"volume": 42}
    json_bytes = json.dumps(payload).encode()
    std_b64 = base64.b64encode(json_bytes).decode().rstrip("=")  # strip padding
    custom_b64 = std_b64.translate(_ENCODE_TABLE)
    wire = gzip.compress(custom_b64.encode())
    assert _decode_payload(wire) == payload


def test_decode_replaces_invalid_utf8_in_peq_metadata() -> None:
    """Malformed optional PEQ text must not prevent device setup.

    Captured from a Luxsin X9: the ``brand`` value of one saved PEQ profile
    contained byte 0xb8, which is not valid UTF-8.
    """
    json_bytes = b'{"volume":42,"peq":[{"name":"Profile","brand":"\xb8"}]}'
    std_b64 = base64.b64encode(json_bytes).decode()
    custom_b64 = std_b64.translate(_ENCODE_TABLE)
    wire = gzip.compress(custom_b64.encode())

    data = _decode_payload(wire)
    assert data["volume"] == 42
    assert data["peq"][0]["brand"] == "\ufffd"


# ---------------------------------------------------------------------------
# Regression fixtures: real captures from a live Luxsin X8.
#
# These strings are copy-pasted from a browser's Network tab (Response
# preview), which transparently gunzips the HTTP response - so what's
# pasted here is already-gunzipped custom-Base64 text, not raw gzip
# bytes. This exercises the "payload doesn't start with the gzip magic
# bytes" branch of _decode_payload.
# ---------------------------------------------------------------------------

_REAL_SYNC_DATA = (
    "nEVbjI2wmIRwkHU8YMirmv6bmI4uUsxDZstbUvuglTf3UsxiXMVhmJGimJCrAsQbUwkulwZyO51r"
    "AsU1XMVFj0VukI2YNImxmMU8YrirmwerAsYbUwk4J5ZhmI23UsxDZrirl5DukJKrAsYbUwZslvfu"
    "Ot6vkrU8YMirjwf3mS6gdSuwNTCrAsYbUvV4mTGhOuZxO0V3UsxDXMVtkJkyj5erArVYmJqFNI1c"
    "IPprXMVqmIGyO3khlv4qmMU8UuLPdHKpUPC3XsQpN3q8UrirjJf3O3qhOIerAsYbUvcgO5VojwVu"
    "jJGxOSuwNTCrAsQbUwk4e5fgl56EUsxDYMirNSGcNI44mSfiO5DqlrU8YMirNSGcNfG2lSerAsKb"
    "UwLsOHU8YEirkTVudI6tkHU8YMirkSRsG5RyOrU8YHirkSRsCJVsUsxiXMVrjIDqOvZuUsxiXMV1"
    "OTUrAsKbUwZhmI2te0GulMU8YHirjv6hmRZhmI2tUsxiXMVtl0LokI2qjvDuUsxDXMVikJRdkIDu"
    "j0CrAsKbUwLulefgjIVbkHU8YMirkIkvkIZ3J5fgjIVbkHU8YMirkIkvkIZ3J0kqOTfuUsxiXMV0"
    "NIG3NR6uOvRrOSerAsKbUwmykTGxJ0kqOTfuUsxEZHirl5ZuOvfokI2qjvDuUsxiXMVFj5fgkf65"
    "jID4kHU8YMirj0Vhl0ZvkIftJ5fgjIVbkHU8YMirj0Vhl0ZvkIftJ0kqOTfuUsxiXMVFmIV0O56v"
    "kJVokI2qjvDuUsxiXMVFmIV0O56vkJVomvRbmIerAsliXMVFmIV0O56vkJVolvR3kHU8YHirl0f"
    "rm56hkvfEJ54ynR63nJLuUsxiXMVFmIV0O56vkJVok5RyOrU8YMirjJftNI6okI2qjvDuUsxiXM"
    "VqOvRbO5mTjIugUsxiXMVFmIV0O56vkJVokSfbjJuoOIRyOrU8YMirl0frm56hkvfEJ5GuOSR2U"
    "sxiXMVsO5Dhlu6uOvRrOSerAsKbUvZhOS6EJ5Vql0Zok5RyOrU8YMirj56bO0VoOIutJ5mqNI1r"
    "AsKbUvZhOS6EJ0GEkIVbkf6wjIugUsxiXMVtjIZIO5D4OIfQNJVuj0CrAsKbUvGqj3uclSftjI2"
    "skHU8YHirOS64kS2ul0ZojvRFl46wjIugUsx0YMirOS64kS2ul0ZomTVujvDuJ5mqNI1rAsliXM"
    "VbO0ftOvfFl463NTVul5qhOSGok5RyOrU8XdQ4XMVbO0ftOvfFl46uOvRrOSerAsKbUvDukR6uO"
    "vRrOSerAsKbUvDukR6EkICrAsU4ZHirOSftJ5mEkIfgUsx3AHirOSftJ5VbmIerAsKbUvV3J0Z3"
    "jJG4lEU8YMirOIRsUsxrYsp8YtC8YPj8Ytj8GtU8CsjrXMVcl5mPO0fgmMU8Y03="
)


def test_decode_real_sync_data_capture() -> None:
    """Regression test against an actual /dev/info.cgi?action=sync capture
    from a live X8 (input=USB, output=RCA, DSP off, no active PEQ/loudness)."""
    data = _decode_payload(_REAL_SYNC_DATA.encode("ascii"))

    assert data["device"] == "Luxsin-X8"
    assert data["volume"] == 169
    assert data["input"] == 0
    assert data["output"] == 1
    assert data["balance"] == 0
    assert data["dsp_enable"] == 1  # per X8-API-README.md: 1 = DSP processing active
    assert data["peqEnable"] == 0
    assert data["loudness_enable"] == 0
    assert data["screenLight"] == 2
    assert data["vu"] == 3
    assert data["vu_count"] == 16
    assert data["bt_status"] == 0
    # Fields not documented in X8-API-README.md, but present on this real device -
    # see the "Subwoofer entities removed" note in README.
    assert data["subwoofer_enable"] == 0
    assert data["subwoofer_value"] == 70


def test_decode_real_sync_peq_capture() -> None:
    """Regression test against an actual ?action=syncPeq capture: a "peq"
    array of saved presets, each with a "name" field used by select.py."""
    real_sync_peq = (
        "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"
    )

    data = _decode_payload(real_sync_peq.encode("ascii"))

    assert data["peqSelect"] == 0
    assert data["peqEnable"] == 0
    peq = data["peq"]
    assert isinstance(peq, list)
    assert len(peq) == 2
    for profile in peq:
        assert "name" in profile
        assert "filters" in profile
