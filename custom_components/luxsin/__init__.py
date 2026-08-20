"""The Luxsin X8/X9 amplifier integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LuxsinClient
from .const import (
    CONF_DEVICE_ID,
    CONF_ENTITY_ID_PREFIX,
    DEFAULT_TIMEOUT,
    DOMAIN,
    normalize_device_id,
)
from .coordinator import LuxsinCoordinator

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.SENSOR,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.SELECT,
]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate legacy entries without changing their entity unique IDs."""
    if entry.version > 1:
        return True

    data = dict(entry.data)
    data.setdefault(CONF_ENTITY_ID_PREFIX, data[CONF_HOST])
    hass.config_entries.async_update_entry(entry, data=data, version=2)
    return True


def _device_id_from_status(coordinator: LuxsinCoordinator) -> str | None:
    """Return the normalized device MAC used as stable config identity."""
    raw = coordinator.data.raw if coordinator.data and coordinator.data.raw else None
    return normalize_device_id(raw.get("mac") if raw else None)


def _async_update_entry_identity(
    hass: HomeAssistant, entry: ConfigEntry, device_id: str | None
) -> None:
    """Persist stable identity while retaining legacy entity identifiers."""
    data = dict(entry.data)
    changed = False

    if CONF_ENTITY_ID_PREFIX not in data:
        data[CONF_ENTITY_ID_PREFIX] = data[CONF_HOST]
        changed = True

    if device_id is not None and data.get(CONF_DEVICE_ID) != device_id:
        data[CONF_DEVICE_ID] = device_id
        changed = True

    unique_id = entry.unique_id
    if device_id is not None and entry.unique_id != device_id:
        duplicate = next(
            (
                candidate
                for candidate in hass.config_entries.async_entries(DOMAIN)
                if candidate.entry_id != entry.entry_id
                and candidate.unique_id == device_id
            ),
            None,
        )
        if duplicate is None:
            unique_id = device_id
            changed = True

    if changed:
        hass.config_entries.async_update_entry(entry, data=data, unique_id=unique_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Luxsin config entry."""
    session = async_get_clientsession(hass)
    client = LuxsinClient(entry.data[CONF_HOST], session, timeout=DEFAULT_TIMEOUT)
    coordinator = LuxsinCoordinator(hass, client)

    await coordinator.async_config_entry_first_refresh()
    _async_update_entry_identity(hass, entry, _device_id_from_status(coordinator))

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Luxsin config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
