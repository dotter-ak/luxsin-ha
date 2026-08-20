"""Entity behavior tests for model-specific and dynamic capabilities."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.const import CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.luxsin.api import LuxsinStatus
from custom_components.luxsin.const import CONF_ENTITY_ID_PREFIX, DOMAIN
from custom_components.luxsin.media_player import LuxsinMediaPlayer
from custom_components.luxsin.select import LuxsinCrossfeedSelect


def _entry(prefix: str = "legacy-host") -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "new-host", CONF_ENTITY_ID_PREFIX: prefix},
    )


def _coordinator(*, model_key: str, input_index: int, crossfeed: int = 0):
    coordinator = MagicMock()
    coordinator.data = LuxsinStatus(
        volume=100,
        input=input_index,
        output=0,
        raw={
            "device": f"Luxsin-{model_key.upper()}",
            "mac": "AA:BB:CC:DD:EE:FF",
            "volume": 100,
            "input": input_index,
            "output": 0,
            "bt_status": 0,
            "crossfeed_value": crossfeed,
        },
        peq_profiles=[],
    )
    coordinator.model_key = model_key
    coordinator.last_update_success = True
    coordinator.async_send_command = AsyncMock()
    coordinator.async_apply_param = AsyncMock()
    return coordinator


async def test_bluetooth_controls_hidden_and_ignored_on_other_inputs() -> None:
    coordinator = _coordinator(model_key="x8", input_index=0)
    entity = LuxsinMediaPlayer(coordinator, _entry())

    bluetooth_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
    )
    assert not entity.supported_features & bluetooth_features

    await entity.async_media_next_track()
    coordinator.async_send_command.assert_not_awaited()


def test_bluetooth_controls_visible_on_bluetooth_input() -> None:
    coordinator = _coordinator(model_key="x8", input_index=4)
    entity = LuxsinMediaPlayer(coordinator, _entry())

    assert entity.supported_features & MediaPlayerEntityFeature.PLAY
    assert entity.supported_features & MediaPlayerEntityFeature.NEXT_TRACK


async def test_x9_exposes_and_applies_custom_crossfeed() -> None:
    coordinator = _coordinator(model_key="x9", input_index=0, crossfeed=3)
    entity = LuxsinCrossfeedSelect(coordinator, _entry())

    assert entity.options[-1] == "Custom"
    assert entity.current_option == "Custom"
    await entity.async_select_option("Custom")
    coordinator.async_apply_param.assert_awaited_once_with("crossfeed_value", 3)


def test_x8_does_not_expose_custom_crossfeed() -> None:
    coordinator = _coordinator(model_key="x8", input_index=0)
    entity = LuxsinCrossfeedSelect(coordinator, _entry())

    assert "Custom" not in entity.options


def test_legacy_entity_unique_id_survives_host_change() -> None:
    coordinator = _coordinator(model_key="x8", input_index=0)
    entity = LuxsinMediaPlayer(coordinator, _entry("original-host"))

    assert entity.unique_id == "luxsin_original-host_media_player"
