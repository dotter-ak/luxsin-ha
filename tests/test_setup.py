"""End-to-end config-entry setup and unload tests."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.const import CONF_HOST, STATE_UNAVAILABLE
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.luxsin.api import LuxsinStatus
from custom_components.luxsin.const import CONF_ENTITY_ID_PREFIX, DOMAIN

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_setup_and_unload_keep_legacy_entity_unique_id(hass) -> None:
    status = LuxsinStatus(
        volume=100,
        input=0,
        output=0,
        raw={
            "device": "Luxsin-X8",
            "mac": "AA:BB:CC:DD:EE:FF",
            "version": "1.0",
            "volume": 100,
            "input": 0,
            "output": 0,
            "audioFormat": "PCM 44.1 kHz",
        },
        peq_profiles=[],
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id="old-host",
        data={
            CONF_HOST: "new-host",
            CONF_ENTITY_ID_PREFIX: "old-host",
        },
    )
    entry.add_to_hass(hass)

    registry = er.async_get(hass)
    existing = registry.async_get_or_create(
        "media_player",
        DOMAIN,
        "luxsin_old-host_media_player",
        suggested_object_id="existing_luxsin",
        config_entry=entry,
    )

    with (
        patch(
            "custom_components.luxsin.api.LuxsinClient.async_get_msg_count",
            return_value=1,
        ),
        patch(
            "custom_components.luxsin.api.LuxsinClient.async_get_full_status",
            return_value=status,
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    entity_id = registry.async_get_entity_id(
        "media_player", DOMAIN, "luxsin_old-host_media_player"
    )
    assert entity_id == existing.entity_id
    assert entry.unique_id == "aabbccddeeff"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    # Home Assistant keeps the registry-backed entity as a restored,
    # unavailable state after unload; it must not be replaced or removed.
    unloaded_state = hass.states.get(entity_id)
    assert unloaded_state is not None
    assert unloaded_state.state == STATE_UNAVAILABLE
