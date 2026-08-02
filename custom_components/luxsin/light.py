"""light entity for the Luxsin X8/X9 amplifier's ambient RGB LED.

led_enable/led_red/led_green/led_blue are documented in X8-API-README.md as
separate writable parameters (0/1 and 0..255 respectively). X9-API-README.md
doesn't mention these fields at all - if a real X9 doesn't return them in
its status payload, has_fields() below means this entity simply won't be
created for it, no per-model code needed. Each channel is written with
its own GET request - there is no combined
"led_color=RRGGBB" parameter.
"""
from __future__ import annotations

import logging

from homeassistant.components.light import ATTR_RGB_COLOR, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
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
    if not has_fields(raw, "led_enable", "led_red", "led_green", "led_blue"):
        _LOGGER.debug("LED fields missing on this device - light entity not created")
        return
    async_add_entities([LuxsinLedLight(coordinator, entry)])


class LuxsinLedLight(LuxsinEntity, LightEntity):
    """Ambient RGB LED on the amplifier."""

    _attr_name = "LED Light"
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_HOST]}_led"

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.raw if self.coordinator.data else None
        if raw is None or "led_enable" not in raw:
            return None
        return bool(raw["led_enable"])

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        raw = self.coordinator.data.raw if self.coordinator.data else None
        if raw is None:
            return None
        r, g, b = raw.get("led_red"), raw.get("led_green"), raw.get("led_blue")
        if r is None or g is None or b is None:
            return None
        return (r, g, b)

    async def async_turn_on(self, **kwargs) -> None:
        rgb = kwargs.get(ATTR_RGB_COLOR)
        if rgb is not None:
            await self.coordinator.async_apply_led(enable=1, rgb=rgb)
        else:
            await self.coordinator.async_apply_led(enable=1)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_apply_led(enable=0)
