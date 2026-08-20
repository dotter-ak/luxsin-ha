"""Config-flow and backwards-compatible identity tests."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.luxsin.api import LuxsinStatus
from custom_components.luxsin.const import (
    CONF_DEVICE_ID,
    CONF_ENTITY_ID_PREFIX,
    DOMAIN,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

MAC = "AA:BB:CC:DD:EE:FF"
DEVICE_ID = "aabbccddeeff"


def _status(mac: str = MAC) -> LuxsinStatus:
    raw = {
        "device": "Luxsin-X8",
        "mac": mac,
        "volume": 100,
        "input": 0,
        "output": 0,
    }
    return LuxsinStatus(volume=100, input=0, output=0, raw=raw, peq_profiles=[])


async def test_user_flow_uses_mac_as_stable_identity(hass) -> None:
    with patch(
        "custom_components.luxsin.config_flow.LuxsinClient.async_get_full_status",
        return_value=_status(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: "192.0.2.10"},
        )

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == DEVICE_ID
    assert result["data"] == {
        CONF_HOST: "192.0.2.10",
        CONF_DEVICE_ID: DEVICE_ID,
        CONF_ENTITY_ID_PREFIX: DEVICE_ID,
    }


async def test_user_flow_rejects_existing_device_by_stored_mac(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="legacy-host",
        data={CONF_HOST: "legacy-host", CONF_DEVICE_ID: DEVICE_ID},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.luxsin.config_flow.LuxsinClient.async_get_full_status",
        return_value=_status(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: "192.0.2.10"},
        )

    assert result["type"] is data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_preserves_legacy_entity_prefix(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id="192.0.2.10",
        data={CONF_HOST: "192.0.2.10"},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    with patch(
        "custom_components.luxsin.config_flow.LuxsinClient.async_get_full_status",
        return_value=_status(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "192.0.2.20"}
        )

    assert result["type"] is data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.unique_id == DEVICE_ID
    assert entry.title == "Luxsin (192.0.2.20)"
    assert entry.data[CONF_HOST] == "192.0.2.20"
    assert entry.data[CONF_DEVICE_ID] == DEVICE_ID
    assert entry.data[CONF_ENTITY_ID_PREFIX] == "192.0.2.10"


async def test_reconfigure_rejects_a_different_device(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=DEVICE_ID,
        data={
            CONF_HOST: "192.0.2.10",
            CONF_DEVICE_ID: DEVICE_ID,
            CONF_ENTITY_ID_PREFIX: "192.0.2.10",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    with patch(
        "custom_components.luxsin.config_flow.LuxsinClient.async_get_full_status",
        return_value=_status("11:22:33:44:55:66"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "192.0.2.20"}
        )

    assert result["type"] is data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "wrong_device"}
    assert entry.data[CONF_HOST] == "192.0.2.10"


async def test_version_one_migration_pins_original_host(hass) -> None:
    from custom_components.luxsin import async_migrate_entry

    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        unique_id="192.0.2.10",
        data={CONF_HOST: "192.0.2.10"},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)
    assert entry.version == 2
    assert entry.data[CONF_ENTITY_ID_PREFIX] == "192.0.2.10"
