"""media_player entity for the Luxsin X8/X9 amplifier.

Volume -> volume_level (0.0-1.0, scaled from the native 0-200 range)
Input -> source / source_list
Output -> sound_mode / sound_mode_list (HA has no dedicated "audio output"
    concept, sound_mode is the closest fit)

source_list/source depend on the model (X8/X9 have different input
enumerations - see const.py: INPUT_NAMES_BY_MODEL) and are resolved
dynamically via coordinator.model_key. sound_mode_list/sound_mode are
identical for both models per X8-API-README.md/X9-API-README.md, so
OUTPUT_NAMES is a single shared list. Either way, an index outside the
known list (the writable range on the wire is wider than the named
enum) falls back to "Input N"/"Output N" instead of returning None.

Bluetooth transport (play/pause/next/prev) and title/artist are confirmed
by X8-API-README.md/X9-API-README.md (bt_status/bt_title/bt_artist in the
status payload; bt_play/bt_next as writable parameters). Neither document
spells out bt_status's numeric meaning though - PLAYING=2/PAUSED=1 below
is confirmed by testing on a real X8 device (the initial guess of
PLAYING=1/PAUSED=2 had them backwards); this hasn't been separately
verified on X9. bt_play is a toggle (not separate play/pause), so
async_media_play/pause only send it when the current bt_status differs
from the target state. These controls only appear when bt_status is
present in the device's status payload, and only reflect Bluetooth
metadata while the active source is Bluetooth.

There is no readable power-state field, but both documents describe a
write-only "power" parameter that powers the device off (any value
triggers it). There is no documented "power on" parameter - once off, the
device (and its Wi-Fi) is unreachable - so only TURN_OFF is exposed.
"""
from __future__ import annotations

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MAX_VOLUME, OUTPUT_NAMES, input_names_for
from .coordinator import LuxsinCoordinator
from .entity import LuxsinEntity, entity_unique_id

_LOGGER = logging.getLogger(__name__)

# Confirmed by testing on a real X8 device - neither X8-API-README.md nor
# X9-API-README.md documents the numeric meaning of bt_status.
_BT_STATUS_PAUSED = 1
_BT_STATUS_PLAYING = 2


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: LuxsinCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LuxsinMediaPlayer(coordinator, entry)])


class LuxsinMediaPlayer(LuxsinEntity, MediaPlayerEntity):
    """media_player entity for the Luxsin X8/X9 amplifier."""

    _attr_name = None  # main entity of the device - no name suffix
    _attr_volume_step = 1 / MAX_VOLUME
    _attr_sound_mode_list = OUTPUT_NAMES

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = entity_unique_id(entry, "media_player")

    @property
    def source_list(self) -> list[str]:
        return input_names_for(self.coordinator.model_key)

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        features = (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.SELECT_SOURCE
            | MediaPlayerEntityFeature.SELECT_SOUND_MODE
            | MediaPlayerEntityFeature.TURN_OFF
        )
        raw = self.coordinator.data.raw if self.coordinator.data else None
        if raw is not None and "bt_status" in raw and self._is_bluetooth_source:
            features |= (
                MediaPlayerEntityFeature.PLAY
                | MediaPlayerEntityFeature.PAUSE
                | MediaPlayerEntityFeature.NEXT_TRACK
                | MediaPlayerEntityFeature.PREVIOUS_TRACK
            )
        return features

    @property
    def _is_bluetooth_source(self) -> bool:
        return self.source == "Bluetooth"

    @property
    def state(self) -> MediaPlayerState:
        if not self.coordinator.last_update_success:
            return MediaPlayerState.OFF
        if self._is_bluetooth_source:
            raw = self.coordinator.data.raw if self.coordinator.data else None
            bt_status = raw.get("bt_status") if raw else None
            if bt_status == _BT_STATUS_PLAYING:
                return MediaPlayerState.PLAYING
            if bt_status == _BT_STATUS_PAUSED:
                return MediaPlayerState.PAUSED
        return MediaPlayerState.ON

    @property
    def volume_level(self) -> float | None:
        if self.coordinator.data is None or self.coordinator.data.volume is None:
            return None
        return self.coordinator.data.volume / MAX_VOLUME

    @property
    def source(self) -> str | None:
        if self.coordinator.data is None or self.coordinator.data.input is None:
            return None
        idx = self.coordinator.data.input
        names = self.source_list
        if 0 <= idx < len(names):
            return names[idx]
        return f"Input {idx}"  # valid on the wire, but outside the known enum

    @property
    def sound_mode(self) -> str | None:
        if self.coordinator.data is None or self.coordinator.data.output is None:
            return None
        idx = self.coordinator.data.output
        if 0 <= idx < len(OUTPUT_NAMES):
            return OUTPUT_NAMES[idx]
        return f"Output {idx}"  # valid on the wire, but outside the known enum

    @property
    def media_title(self) -> str | None:
        if not self._is_bluetooth_source or self.coordinator.data is None:
            return None
        raw = self.coordinator.data.raw
        return raw.get("bt_title") if raw else None

    @property
    def media_artist(self) -> str | None:
        if not self._is_bluetooth_source or self.coordinator.data is None:
            return None
        raw = self.coordinator.data.raw
        return raw.get("bt_artist") if raw else None

    @property
    def extra_state_attributes(self) -> dict:
        """Full decoded JSON, kept around for fields not yet mapped to a
        dedicated entity."""
        if self.coordinator.data is None or self.coordinator.data.raw is None:
            return {}
        return {"raw_status": self.coordinator.data.raw}

    async def async_set_volume_level(self, volume: float) -> None:
        await self.coordinator.async_apply_volume(round(volume * MAX_VOLUME))

    async def async_select_source(self, source: str) -> None:
        names = self.source_list
        if source not in names:
            _LOGGER.warning("Unknown Luxsin input: %s", source)
            return
        await self.coordinator.async_apply_input(names.index(source))

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        if sound_mode not in OUTPUT_NAMES:
            _LOGGER.warning("Unknown Luxsin output: %s", sound_mode)
            return
        await self.coordinator.async_apply_output(OUTPUT_NAMES.index(sound_mode))

    async def async_media_play(self) -> None:
        if not self._is_bluetooth_source:
            return
        raw = self.coordinator.data.raw if self.coordinator.data else None
        if raw is not None and raw.get("bt_status") != _BT_STATUS_PLAYING:
            await self.coordinator.async_send_command("bt_play", 1)

    async def async_media_pause(self) -> None:
        if not self._is_bluetooth_source:
            return
        raw = self.coordinator.data.raw if self.coordinator.data else None
        if raw is not None and raw.get("bt_status") == _BT_STATUS_PLAYING:
            await self.coordinator.async_send_command("bt_play", 1)

    async def async_media_next_track(self) -> None:
        if self._is_bluetooth_source:
            await self.coordinator.async_send_command("bt_next", 1)

    async def async_media_previous_track(self) -> None:
        if self._is_bluetooth_source:
            await self.coordinator.async_send_command("bt_next", 0)

    async def async_turn_off(self) -> None:
        """Power off the device.

        Both X8-API-README.md and X9-API-README.md: "power | any value |
        Power off." There is no documented way to power it back on
        remotely.
        """
        await self.coordinator.async_send_command("power", 1)
