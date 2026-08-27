"""Sensor entities for the Luxsin X8/X9 amplifier."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import LuxsinCoordinator
from .entity import LuxsinEntity, entity_unique_id, has_fields

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LuxsinCoordinator = hass.data[DOMAIN][entry.entry_id]
    raw = coordinator.data.raw if coordinator.data else None
    entities: list[SensorEntity] = [LuxsinVolumeRawSensor(coordinator, entry)]

    if has_fields(raw, "audioFormat"):
        entities.append(LuxsinAudioFormatSensor(coordinator, entry))
    else:
        _LOGGER.debug("audioFormat field missing on this device - sensor not created")

    async_add_entities(entities)


class LuxsinVolumeRawSensor(LuxsinEntity, SensorEntity):
    """Native device volume on its unscaled 0..200 range."""

    _attr_name = "Volume Raw"
    _attr_icon = "mdi:volume-high"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = True
    _attr_native_unit_of_measurement = None
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = entity_unique_id(entry, "volume_raw")

    @property
    def available(self) -> bool:
        """Return unavailable until the coordinator has current status data."""
        return super().available and self.coordinator.data is not None

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.volume


class LuxsinAudioFormatSensor(LuxsinEntity, SensorEntity):
    """Currently detected audio format."""

    _attr_name = "Audio Format"
    _attr_icon = "mdi:waveform"

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = entity_unique_id(entry, "audio_format")

    @property
    def native_value(self) -> str | None:
        if self.coordinator.data is None or self.coordinator.data.raw is None:
            return None
        value = self.coordinator.data.raw.get("audioFormat")
        return value.strip() if isinstance(value, str) else value
