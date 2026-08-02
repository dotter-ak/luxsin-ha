"""number entities for the Luxsin X8/X9 amplifier.

Balance range/scale is confirmed identical for both models by
X8-API-README.md/X9-API-README.md: raw device values are -150..150,
displayed by the official UI as -15.0..+15.0 dB. This entity works
directly in dB and converts to/from the raw integer.

Screen Brightness (screenLight) is likewise confirmed identical for both
models as a 0..2 discrete setting ("Set LCD brightness") - exposed as a
plain integer rather than inventing specific level names (e.g.
"Low/Medium/High") that aren't documented. The raw device value is
inverted (0 = brightest, 2 = dimmest), so LuxsinScreenBrightnessNumber
flips it in both directions to give an intuitive HA slider.

Note: subwoofer_value/subwoofer_gain fields exist in the X8's status
payload (observed via live capture) but are NOT exposed as entities here -
the X8 has no subwoofer output, so on X8 these fields have no audible
effect. (X9-API-README.md confirms X9 has a much more built-out
subwoofer feature set - crossover, gain, slope, HPF/LPF, delay, etc. -
which isn't implemented here either, since it wasn't asked for when X9
support was added. Still visible in the `raw_status` attribute on
media_player if you want to inspect the values.)
"""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BALANCE_MAX_DB,
    BALANCE_MIN_DB,
    BALANCE_SCALE,
    BALANCE_STEP_DB,
    DOMAIN,
    SCREEN_BRIGHTNESS_MAX,
    SCREEN_BRIGHTNESS_MIN,
)
from .coordinator import LuxsinCoordinator
from .entity import LuxsinEntity, has_fields

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LuxsinCoordinator = hass.data[DOMAIN][entry.entry_id]
    raw = coordinator.data.raw if coordinator.data else None

    entities: list[NumberEntity] = []
    if has_fields(raw, "balance"):
        entities.append(LuxsinBalanceNumber(coordinator, entry))
    else:
        _LOGGER.debug("balance field missing on this device - number entity not created")

    if has_fields(raw, "screenLight"):
        entities.append(LuxsinScreenBrightnessNumber(coordinator, entry))
    else:
        _LOGGER.debug("screenLight field missing on this device - number entity not created")

    if entities:
        async_add_entities(entities)


class LuxsinBalanceNumber(LuxsinEntity, NumberEntity):
    """L/R balance, in dB (raw device field is tenths of a dB, -150..150)."""

    _param = "balance"
    _attr_name = "Balance"
    _attr_icon = "mdi:equalizer"
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = "dB"
    _attr_native_min_value = BALANCE_MIN_DB
    _attr_native_max_value = BALANCE_MAX_DB
    _attr_native_step = BALANCE_STEP_DB

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_HOST]}_{self._param}"

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.raw if self.coordinator.data else None
        if raw is None or raw.get(self._param) is None:
            return None
        return raw[self._param] / BALANCE_SCALE

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_apply_param(self._param, round(value * BALANCE_SCALE))


class LuxsinScreenBrightnessNumber(LuxsinEntity, NumberEntity):
    """Screen (LCD) brightness, a 0..2 discrete level (screenLight).

    The device's raw screenLight field is inverted relative to what a
    brightness control should feel like (raw 0 = brightest, raw 2 =
    dimmest). This entity flips the value so the HA slider behaves as
    expected (0 = dimmest, 2 = brightest), converting back to the raw
    scale when writing to the device.
    """

    _param = "screenLight"
    _attr_name = "Screen Brightness"
    _attr_icon = "mdi:brightness-6"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = SCREEN_BRIGHTNESS_MIN
    _attr_native_max_value = SCREEN_BRIGHTNESS_MAX
    _attr_native_step = 1

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_HOST]}_{self._param}"

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.data.raw if self.coordinator.data else None
        if raw is None or raw.get(self._param) is None:
            return None
        return SCREEN_BRIGHTNESS_MAX - raw[self._param]

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_apply_param(
            self._param, int(SCREEN_BRIGHTNESS_MAX - value)
        )
