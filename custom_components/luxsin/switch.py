"""switch entities for the Luxsin X8/X9 amplifier.

Each switch maps one boolean (0/1) JSON field to a plain on/off toggle,
written through the same /dev/info.cgi?action=setting&<param>=<value>
mechanism as volume/input/output.

LuxsinDspSwitch is exposed as "DSP Bypass" rather than "DSP": the raw
dsp_enable field means "DSP processing active" (1=active - neither
X8-API-README.md nor X9-API-README.md states the polarity explicitly, both
just phrase it like every other "_enable" flag), but "Bypass" reads more
intuitively as ON = processing is skipped. So this entity's
is_on/turn_on/turn_off are inverted relative to the raw dsp_enable value -
ON here means dsp_enable=0 on the wire.

peqEnable follows the standard 1=enabled/0=disabled convention used
throughout both documents, so LuxsinPeqEnableSwitch uses the shared base
class as-is.

Note: a subwoofer_enable switch used to be exposed here too, but the X8
has no subwoofer output, so on X8 the field has no audible effect.
(X9-API-README.md confirms X9 has a fully-built-out subwoofer feature -
still not implemented here, since it wasn't asked for when X9 support
was added.)
"""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, EntityCategory
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

    candidates: list[tuple[str, type[SwitchEntity]]] = [
        ("dsp_enable", LuxsinDspSwitch),
        ("peqEnable", LuxsinPeqEnableSwitch),
        ("audio_enable", LuxsinEffectsSwitch),
        ("effect_enable", LuxsinStyleEnableSwitch),
        ("width_enable", LuxsinStereoWidthEnableSwitch),
        ("crossfeed_enable", LuxsinCrossfeedEnableSwitch),
        ("color_enable", LuxsinToneEnableSwitch),
        ("loudness_enable", LuxsinLoudnessEnableSwitch),
    ]
    entities = []
    for field, cls in candidates:
        if has_fields(raw, field):
            entities.append(cls(coordinator, entry))
        else:
            _LOGGER.debug("%s field missing on this device - switch not created", field)

    if entities:
        async_add_entities(entities)


class _LuxsinParamSwitch(LuxsinEntity, SwitchEntity):
    """Shared base: one boolean (0/1) JSON field <-> one switch."""

    _param: str = ""

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_HOST]}_{self._param}"

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.raw if self.coordinator.data else None
        if raw is None or self._param not in raw:
            return None
        return bool(raw[self._param])

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_apply_param(self._param, 1)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_apply_param(self._param, 0)


class LuxsinDspSwitch(_LuxsinParamSwitch):
    """DSP Bypass: ON means the DSP processing chain is bypassed.

    Inverted relative to the raw "dsp_enable" field (1=processing active
    per X8-API-README.md), so this reads as "Bypass" rather than "DSP enabled".
    """

    _param = "dsp_enable"
    _attr_name = "DSP Bypass"
    _attr_icon = "mdi:debug-step-over"
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.raw if self.coordinator.data else None
        if raw is None or self._param not in raw:
            return None
        return not bool(raw[self._param])

    async def async_turn_on(self, **kwargs) -> None:
        # "Bypass ON" means DSP processing OFF -> dsp_enable=0
        await self.coordinator.async_apply_param(self._param, 0)

    async def async_turn_off(self, **kwargs) -> None:
        # "Bypass OFF" means DSP processing ON -> dsp_enable=1
        await self.coordinator.async_apply_param(self._param, 1)


class LuxsinPeqEnableSwitch(_LuxsinParamSwitch):
    """Master on/off for parametric EQ processing.

    Separate from the "PEQ Profile" select entity (select.py), which
    picks *which* saved preset is active - this just turns PEQ
    processing on/off entirely, regardless of which preset is selected.

    Exposed as a regular Controls entity (no entity_category) rather than
    Configuration, since it's a day-to-day on/off toggle rather than a
    setup/config-time setting.
    """

    _param = "peqEnable"
    _attr_name = "PEQ"
    _attr_icon = "mdi:equalizer"


class LuxsinEffectsSwitch(_LuxsinParamSwitch):
    """Effects: master on/off for the whole DSP audio-processing chain
    (Style, Stereo width, Crossfeed, Tone, Loudness).

    Turning this off makes every entity in that group unavailable, since
    all of them declare "audio_enable" as a parent in `_parent_params`
    (see entity.py).
    """

    _param = "audio_enable"
    _attr_name = "Effects"
    _attr_icon = "mdi:tune-variant"
    _attr_entity_category = EntityCategory.CONFIG


class LuxsinStyleEnableSwitch(_LuxsinParamSwitch):
    """Style: enable/disable the effect_value EQ preset.

    Child of Effects (audio_enable); its own child is the Style value
    select entity (effect_value, see select.py).
    """

    _param = "effect_enable"
    _attr_name = "Style"
    _attr_icon = "mdi:tune"
    _attr_entity_category = EntityCategory.CONFIG
    _parent_params = ("audio_enable",)


class LuxsinStereoWidthEnableSwitch(_LuxsinParamSwitch):
    """Stereo width: enable/disable the width_value soundstage effect.

    Child of Effects (audio_enable); its own child is the Stereo width
    value number entity (width_value, see number.py).
    """

    _param = "width_enable"
    _attr_name = "Stereo width"
    _attr_icon = "mdi:arrow-expand-horizontal"
    _attr_entity_category = EntityCategory.CONFIG
    _parent_params = ("audio_enable",)


class LuxsinCrossfeedEnableSwitch(_LuxsinParamSwitch):
    """Crossfeed: enable/disable the crossfeed_value BS2B preset.

    Child of Effects (audio_enable); its own child is the Crossfeed value
    select entity (crossfeed_value, see select.py).
    """

    _param = "crossfeed_enable"
    _attr_name = "Crossfeed"
    _attr_icon = "mdi:swap-horizontal"
    _attr_entity_category = EntityCategory.CONFIG
    _parent_params = ("audio_enable",)


class LuxsinToneEnableSwitch(_LuxsinParamSwitch):
    """Tone: enable/disable the bass/mid/treble color EQ.

    Child of Effects (audio_enable); its children are the Bass/Mid/Treble
    number entities (color_bass_gain/color_mid_gain/color_treble_gain, see
    number.py).
    """

    _param = "color_enable"
    _attr_name = "Tone"
    _attr_icon = "mdi:equalizer-outline"
    _attr_entity_category = EntityCategory.CONFIG
    _parent_params = ("audio_enable",)


class LuxsinLoudnessEnableSwitch(_LuxsinParamSwitch):
    """Loudness: enable/disable the loudness compensation curve.

    Child of Effects (audio_enable); its children are the Threshold/Bass/
    Treble number entities (loudness_threshold_gain/loudness_bass_gain/
    loudness_treble_gain, see number.py).
    """

    _param = "loudness_enable"
    _attr_name = "Loudness"
    _attr_icon = "mdi:volume-vibrate"
    _attr_entity_category = EntityCategory.CONFIG
    _parent_params = ("audio_enable",)
