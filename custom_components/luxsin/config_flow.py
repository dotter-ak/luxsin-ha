"""Config flow for the Luxsin X8/X9 integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LuxsinClient, LuxsinError
from .const import (
    CONF_DEVICE_ID,
    CONF_ENTITY_ID_PREFIX,
    DOMAIN,
    normalize_device_id,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})


class LuxsinConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Luxsin X8/X9."""

    VERSION = 2

    def _device_id_is_configured(
        self, device_id: str, *, ignore_entry_id: str | None = None
    ) -> bool:
        """Check both migrated and not-yet-migrated config entries."""
        return any(
            candidate.entry_id != ignore_entry_id
            and (
                candidate.unique_id == device_id
                or candidate.data.get(CONF_DEVICE_ID) == device_id
            )
            for candidate in self.hass.config_entries.async_entries(DOMAIN)
        )

    async def _async_device_id_for_host(self, host: str) -> str:
        """Validate a Luxsin host and return its stable device identity."""
        session = async_get_clientsession(self.hass)
        client = LuxsinClient(host, session)
        status = await client.async_get_full_status()
        raw = status.raw or {}
        device_id = normalize_device_id(raw.get("mac"))
        if device_id is None:
            raise LuxsinError("Device status did not contain a valid MAC address")
        return device_id

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            try:
                device_id = await self._async_device_id_for_host(host)
            except LuxsinError:
                _LOGGER.debug("Could not connect to %s", host, exc_info=True)
                errors["base"] = "cannot_connect"
            else:
                if self._device_id_is_configured(device_id):
                    return self.async_abort(reason="already_configured")
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Luxsin ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_DEVICE_ID: device_id,
                        CONF_ENTITY_ID_PREFIX: device_id,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Update the network address without replacing existing entities."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            try:
                device_id = await self._async_device_id_for_host(host)
            except LuxsinError:
                _LOGGER.debug("Could not connect to %s", host, exc_info=True)
                errors["base"] = "cannot_connect"
            else:
                known_device_id = entry.data.get(CONF_DEVICE_ID)
                if known_device_id is not None and known_device_id != device_id:
                    errors["base"] = "wrong_device"
                elif self._device_id_is_configured(
                    device_id, ignore_entry_id=entry.entry_id
                ):
                    errors["base"] = "already_configured"
                else:
                    # Preserve the original host-derived prefix for legacy
                    # entries. Only the connection address and config-entry
                    # identity change; entity unique IDs remain untouched.
                    entity_id_prefix = entry.data.get(
                        CONF_ENTITY_ID_PREFIX, entry.data[CONF_HOST]
                    )
                    return self.async_update_reload_and_abort(
                        entry,
                        unique_id=device_id,
                        title=f"Luxsin ({host})",
                        data_updates={
                            CONF_HOST: host,
                            CONF_DEVICE_ID: device_id,
                            CONF_ENTITY_ID_PREFIX: entity_id_prefix,
                        },
                    )

        schema = vol.Schema(
            {vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str}
        )
        return self.async_show_form(
            step_id="reconfigure", data_schema=schema, errors=errors
        )
