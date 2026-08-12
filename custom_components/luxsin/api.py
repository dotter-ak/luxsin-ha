"""Low-level client for the Luxsin X8/X9 unofficial HTTP API.

Protocol reference: X8-API-README.md / X9-API-README.md (manufacturer-provided,
derived from the luxsin_x8/luxsin_x9 firmware source respectively). Both
models share the same wire protocol (endpoints, custom Base64 alphabet,
and most fields) - see const.py for the model-specific differences that
do exist (mainly the input enumeration).

    GET /dev/info.cgi?action=sync
        -> response body: gzip(custom_base64(JSON)). The decoded JSON
           includes the common status fields plus a "peq" array of saved
           PEQ presets. ("syncData" returns the same status fields without
           "peq" - we always want both, so "sync" is used directly.)

    GET /dev/info.cgi?action=setting&<param>=<value>
        -> writes one or more parameters (multiple can be combined in one
           request). A successful response is the plain text
           "Settings updated".

    GET /msgCount
        -> plain integer change counter. Poll this cheaply and only fetch
           a full /dev/info.cgi?action=sync when the value changes.

The custom Base64 alphabet is just a permutation of the standard alphabet:
translate character-by-character, then decode as normal Base64.
"""
from __future__ import annotations

import asyncio
import base64
import binascii
import gzip
import json
import logging
from dataclasses import dataclass
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Device-specific alphabet -> standard Base64 alphabet, position-for-position.
_CUSTOM_ALPHABET = "KLMPQRSTUVWXYZABCGHdefIJjkNOlmnopqrstuvwxyzabcghiDEF34501289+67/"
_STANDARD_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_REMAP_TABLE = str.maketrans(_CUSTOM_ALPHABET, _STANDARD_ALPHABET)


class LuxsinError(Exception):
    """Base error for the Luxsin client."""


class LuxsinConnectionError(LuxsinError):
    """The device could not be reached (network, timeout, HTTP error)."""


class LuxsinProtocolError(LuxsinError):
    """A response was received but could not be decompressed/decoded/parsed."""


@dataclass
class LuxsinStatus:
    """Parsed device status."""

    volume: int | None = None
    input: int | None = None
    output: int | None = None
    # Full decoded JSON, kept around for fields not mapped to a typed
    # attribute or a dedicated entity yet.
    raw: dict[str, Any] | None = None
    # Saved PEQ presets, from the same "sync" response as `raw`.
    peq_profiles: list[dict[str, Any]] | None = None


def _decode_payload(raw_body: bytes) -> dict[str, Any]:
    """gzip(custom-base64(JSON)) -> dict."""
    if raw_body[:2] == b"\x1f\x8b":
        try:
            payload = gzip.decompress(raw_body)
        except OSError as err:
            raise LuxsinProtocolError(f"gzip decompress failed: {err}") from err
    else:
        # In case something in front of the device (proxy, aiohttp itself)
        # already transparently decompressed a gzip Content-Encoding.
        payload = raw_body

    try:
        remapped_text = payload.decode("ascii").strip()
    except UnicodeDecodeError as err:
        raise LuxsinProtocolError(f"unexpected payload encoding: {err}") from err

    b64_text = remapped_text.translate(_REMAP_TABLE)
    b64_text += "=" * (-len(b64_text) % 4)  # restore Base64 padding if missing

    try:
        json_bytes = base64.b64decode(b64_text)
    except (ValueError, binascii.Error) as err:
        raise LuxsinProtocolError(f"base64 decode failed: {err}") from err

    # Some X9 firmware versions return invalid UTF-8 in optional PEQ profile
    # metadata (for example, a malformed ``brand`` value). Preserve the valid
    # status data and replace only those undecodable characters instead of
    # preventing the whole integration from starting.
    try:
        data = json.loads(json_bytes.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as err:
        raise LuxsinProtocolError(f"invalid JSON: {err}") from err

    if not isinstance(data, dict):
        raise LuxsinProtocolError(f"expected JSON object, got {type(data)}")
    return data


class LuxsinClient:
    """Client for a single Luxsin X8 or X9 amplifier."""

    def __init__(
        self,
        host: str,
        session: aiohttp.ClientSession,
        timeout: float = 3.0,
    ) -> None:
        self._host = host
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    @property
    def host(self) -> str:
        return self._host

    async def async_get_msg_count(self) -> int:
        """GET /msgCount - cheap change counter used for polling."""
        url = f"http://{self._host}/msgCount"
        try:
            async with self._session.get(url, timeout=self._timeout) as resp:
                resp.raise_for_status()
                text = await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise LuxsinConnectionError(str(err)) from err

        try:
            return int(text.strip())
        except ValueError as err:
            raise LuxsinProtocolError(f"unexpected msgCount body: {text!r}") from err

    async def async_get_full_status(self) -> LuxsinStatus:
        """GET /dev/info.cgi?action=sync - status fields plus saved PEQ
        presets in a single request (per X8-API-README.md, "sync" returns the
        common status fields plus "peq"; "syncData" omits "peq")."""
        url = f"http://{self._host}/dev/info.cgi?action=sync"
        try:
            async with self._session.get(url, timeout=self._timeout) as resp:
                resp.raise_for_status()
                body = await resp.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise LuxsinConnectionError(str(err)) from err

        data = _decode_payload(body)
        peq_profiles = data.get("peq")
        return LuxsinStatus(
            volume=data.get("volume"),
            input=data.get("input"),
            output=data.get("output"),
            raw=data,
            peq_profiles=peq_profiles if isinstance(peq_profiles, list) else [],
        )

    async def async_set_param(self, param: str, value: int) -> None:
        """GET /dev/info.cgi?action=setting&<param>=<value>."""
        url = f"http://{self._host}/dev/info.cgi?action=setting&{param}={value}"
        try:
            async with self._session.get(url, timeout=self._timeout) as resp:
                resp.raise_for_status()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise LuxsinConnectionError(str(err)) from err
