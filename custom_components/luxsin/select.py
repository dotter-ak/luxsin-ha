"""select entities for the Luxsin X8/X9 amplifier: input, output, VU meter
style, and PEQ preset.

Input/output are already selectable through the media_player entity
(source/sound_mode), but a standalone select entity is often more
convenient for dashboards and automations that don't otherwise deal with
the media_player domain. Both write through the same coordinator methods
media_player uses, so state stays consistent between the two. Input
options depend on the model (see const.py: INPUT_NAMES_BY_MODEL); output
options are identical for both models.

VU meter style ("vu", 0..15) picks between 16 built-in display styles
(X8-API-README.md: "vu_count" confirms 16 styles exist) - the document doesn't
name them individually, so options are generic "Style N" labels rather
than invented descriptive names.

The PEQ preset list comes from /dev/info.cgi?action=sync ("peq" array,
presets saved on the device). The "peqSelect" field in the status payload
holds the index of the active preset, and is also a documented writable
parameter (X8-API-README.md: "peqSelect | 0..(peq_count-1) | Select PEQ preset."),
so selecting an option here writes back through the same field.
"""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, OUTPUT_NAMES, input_names_for
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

    entities: list[SelectEntity] = []

    if has_fields(raw, "input"):
        entities.append(LuxsinInputSelect(coordinator, entry))
    else:
        _LOGGER.debug("input field missing on this device - select entity not created")

    if has_fields(raw, "output"):
        entities.append(LuxsinOutputSelect(coordinator, entry))
    else:
        _LOGGER.debug("output field missing on this device - select entity not created")

    if has_fields(raw, "vu"):
        entities.append(LuxsinVuStyleSelect(coordinator, entry))
    else:
        _LOGGER.debug("vu field missing on this device - select entity not created")

    if coordinator.data and coordinator.data.peq_profiles:
        entities.append(LuxsinPeqSelect(coordinator, entry))
    else:
        _LOGGER.debug("No PEQ presets returned by this device - select entity not created")

    if entities:
        async_add_entities(entities)


class LuxsinInputSelect(LuxsinEntity, SelectEntity):
    """Choose the active input. Mirrors media_player's source, as a
    standalone entity."""

    _attr_name = "Input"
    _attr_icon = "mdi:import"

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_HOST]}_input_select"

    @property
    def options(self) -> list[str]:
        return input_names_for(self.coordinator.model_key)

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None or self.coordinator.data.input is None:
            return None
        idx = self.coordinator.data.input
        names = self.options
        if 0 <= idx < len(names):
            return names[idx]
        return f"Input {idx}"  # valid on the wire, but outside the known enum

    async def async_select_option(self, option: str) -> None:
        names = self.options
        if option not in names:
            _LOGGER.warning("Unknown Luxsin input: %s", option)
            return
        await self.coordinator.async_apply_input(names.index(option))


class LuxsinOutputSelect(LuxsinEntity, SelectEntity):
    """Choose the active output. Mirrors media_player's sound_mode, as a
    standalone entity."""

    _attr_name = "Output"
    _attr_icon = "mdi:export"
    _attr_options = OUTPUT_NAMES

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_HOST]}_output_select"

    @property
    def current_option(self) -> str | None:
        if self.coordinator.data is None or self.coordinator.data.output is None:
            return None
        idx = self.coordinator.data.output
        if 0 <= idx < len(OUTPUT_NAMES):
            return OUTPUT_NAMES[idx]
        return f"Output {idx}"  # valid on the wire, but outside the known enum

    async def async_select_option(self, option: str) -> None:
        if option not in OUTPUT_NAMES:
            _LOGGER.warning("Unknown Luxsin output: %s", option)
            return
        await self.coordinator.async_apply_output(OUTPUT_NAMES.index(option))


# X8-API-README.md: vu_count = 16 (firmware-defined), vu writable range is 0..15.
_VU_STYLE_COUNT = 16
_VU_STYLE_NAMES = [f"Style {i}" for i in range(_VU_STYLE_COUNT)]


class LuxsinVuStyleSelect(LuxsinEntity, SelectEntity):
    """Choose the VU meter display style.

    X8-API-README.md documents 16 built-in styles (field "vu") but doesn't name
    them individually, so options are generic "Style N" labels rather
    than invented descriptive names.
    """

    _attr_name = "VU Meter Style"
    _attr_icon = "mdi:gauge"
    _attr_options = _VU_STYLE_NAMES

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_HOST]}_vu_select"

    @property
    def current_option(self) -> str | None:
        raw = self.coordinator.data.raw if self.coordinator.data else None
        if raw is None or raw.get("vu") is None:
            return None
        idx = raw["vu"]
        if 0 <= idx < len(_VU_STYLE_NAMES):
            return _VU_STYLE_NAMES[idx]
        return f"Style {idx}"  # valid on the wire, but outside the documented range

    async def async_select_option(self, option: str) -> None:
        if option not in _VU_STYLE_NAMES:
            _LOGGER.warning("Unknown VU style option: %s", option)
            return
        await self.coordinator.async_apply_param("vu", _VU_STYLE_NAMES.index(option))


class LuxsinPeqSelect(LuxsinEntity, SelectEntity):
    """Choose a PEQ preset saved on the device."""

    _attr_name = "PEQ Profile"
    _attr_icon = "mdi:equalizer"

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_HOST]}_peq_select"

    @property
    def _profiles(self) -> list[dict]:
        if self.coordinator.data is None:
            return []
        return self.coordinator.data.peq_profiles or []

    @property
    def options(self) -> list[str]:
        return [p.get("name") or f"Slot {i}" for i, p in enumerate(self._profiles)]

    @property
    def current_option(self) -> str | None:
        profiles = self._profiles
        raw = self.coordinator.data.raw if self.coordinator.data else None
        if not profiles or raw is None:
            return None
        idx = raw.get("peqSelect")
        if isinstance(idx, int) and 0 <= idx < len(profiles):
            return profiles[idx].get("name") or f"Slot {idx}"
        return None

    async def async_select_option(self, option: str) -> None:
        for i, profile in enumerate(self._profiles):
            name = profile.get("name") or f"Slot {i}"
            if name == option:
                await self.coordinator.async_apply_peq_select(i)
                return
        _LOGGER.warning("Unknown PEQ profile: %s", option)
