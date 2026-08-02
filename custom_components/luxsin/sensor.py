"""sensor entities for the Luxsin X8/X9 amplifier.

Currently a single sensor - audioFormat (e.g. "PCM 44.1 kHz"), which the
device reports for the currently active input. Confirmed in both
X8-API-README.md and X9-API-README.md.
"""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
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
    if not has_fields(raw, "audioFormat"):
        _LOGGER.debug("audioFormat field missing on this device - sensor not created")
        return
    async_add_entities([LuxsinAudioFormatSensor(coordinator, entry)])


class LuxsinAudioFormatSensor(LuxsinEntity, SensorEntity):
    """Currently detected audio format."""

    _attr_name = "Audio Format"
    _attr_icon = "mdi:waveform"

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_HOST]}_audio_format"

    @property
    def native_value(self) -> str | None:
        if self.coordinator.data is None or self.coordinator.data.raw is None:
            return None
        value = self.coordinator.data.raw.get("audioFormat")
        return value.strip() if isinstance(value, str) else value
