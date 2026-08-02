"""DataUpdateCoordinator for the Luxsin X8/X9 integration.

Polls /msgCount (cheap) on a fixed interval. The full status and PEQ
presets (/dev/info.cgi?action=sync) are only fetched when the counter
changes.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LuxsinClient, LuxsinError, LuxsinStatus
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, normalize_model_key

_LOGGER = logging.getLogger(__name__)


class LuxsinCoordinator(DataUpdateCoordinator[LuxsinStatus]):
    """Coordinator polling a single Luxsin X8 or X9 amplifier."""

    def __init__(self, hass: HomeAssistant, client: LuxsinClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self._last_msg_count: int | None = None

    @property
    def model_key(self) -> str:
        """'x8' / 'x9' / DEFAULT_MODEL_KEY fallback, from the "device" field."""
        raw = self.data.raw if self.data and self.data.raw else None
        return normalize_model_key(raw.get("device") if raw else None)

    async def _async_update_data(self) -> LuxsinStatus:
        try:
            msg_count = await self.client.async_get_msg_count()
            if self.data is not None and msg_count == self._last_msg_count:
                # Nothing changed on the device since the last full fetch.
                return self.data
            status = await self.client.async_get_full_status()
            self._last_msg_count = msg_count
            return status
        except LuxsinError as err:
            raise UpdateFailed(str(err)) from err

    async def async_apply_volume(self, volume: int) -> None:
        """Write volume and optimistically update local state."""
        await self.client.async_set_param("volume", volume)
        if self.data is not None:
            self.data.volume = volume
            if self.data.raw is not None:
                self.data.raw["volume"] = volume
            self.async_set_updated_data(self.data)

    async def async_apply_input(self, index: int) -> None:
        await self.client.async_set_param("input", index)
        if self.data is not None:
            self.data.input = index
            if self.data.raw is not None:
                self.data.raw["input"] = index
            self.async_set_updated_data(self.data)

    async def async_apply_output(self, index: int) -> None:
        await self.client.async_set_param("output", index)
        if self.data is not None:
            self.data.output = index
            if self.data.raw is not None:
                self.data.raw["output"] = index
            self.async_set_updated_data(self.data)

    async def async_apply_param(self, param: str, value: int) -> None:
        """Generic setter: one JSON status field <-> one device write, with
        an optimistic local update so entities reflect the change
        immediately instead of waiting for the next poll cycle.

        Used by number/switch/select entities that map a simple field
        directly, without a dedicated typed attribute on LuxsinStatus
        (balance, dsp_enable, loudness_enable, peqSelect, ...).
        """
        await self.client.async_set_param(param, value)
        if self.data is not None and self.data.raw is not None:
            self.data.raw[param] = value
            self.async_set_updated_data(self.data)

    async def async_apply_peq_select(self, index: int) -> None:
        """Select a saved PEQ preset by index into peq_profiles.

        Confirmed as a writable parameter by X8-API-README.md:
        "peqSelect | 0..(peq_count-1) | Select PEQ preset."
        """
        await self.async_apply_param("peqSelect", index)

    async def async_apply_led(
        self, enable: int | None = None, rgb: tuple[int, int, int] | None = None
    ) -> None:
        """Turn the ambient LED on/off and/or set its RGB color.

        Each channel is written with its own GET request (led_enable, then
        led_red/led_green/led_blue) - X8-API-README.md documents them as separate
        writable parameters; there is no combined "led_color" parameter.
        """
        if enable is not None:
            await self.client.async_set_param("led_enable", enable)
        if rgb is not None:
            r, g, b = rgb
            await self.client.async_set_param("led_red", r)
            await self.client.async_set_param("led_green", g)
            await self.client.async_set_param("led_blue", b)

        if self.data is not None and self.data.raw is not None:
            if enable is not None:
                self.data.raw["led_enable"] = enable
            if rgb is not None:
                self.data.raw["led_red"] = rgb[0]
                self.data.raw["led_green"] = rgb[1]
                self.data.raw["led_blue"] = rgb[2]
            self.async_set_updated_data(self.data)

    async def async_send_command(self, param: str, value: int) -> None:
        """Send a one-shot command (not a status field), without an
        optimistic local update.

        Used for action triggers rather than status fields returned by
        "sync" - e.g. bt_play/bt_next (Bluetooth transport) and power
        (power off).
        """
        await self.client.async_set_param(param, value)
