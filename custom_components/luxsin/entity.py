"""Shared base entity for all Luxsin platforms.

Centralizes DeviceInfo construction so media_player, sensor, etc. are all
grouped under one HA device with a consistent model/MAC.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, format_mac
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ENTITY_ID_PREFIX, DOMAIN
from .coordinator import LuxsinCoordinator


class LuxsinEntity(CoordinatorEntity[LuxsinCoordinator]):
    """Base class providing a shared DeviceInfo built from the latest raw status.

    Also supports a simple parent/child availability chain: subclasses can
    set `_parent_params` to a tuple of raw-status boolean field names (e.g.
    ("audio_enable", "effect_enable")) that must ALL be truthy for this
    entity to be considered available. Used by the Effects group (Style,
    Stereo width, Crossfeed, Tone, Loudness and their children) so turning
    off a parent switch visibly deactivates its descendants instead of
    leaving them interactable but meaningless.
    """

    _attr_has_entity_name = True
    _parent_params: tuple[str, ...] = ()

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        host = entry.data[CONF_HOST]
        identity = entry.data.get(CONF_ENTITY_ID_PREFIX, host)
        raw = coordinator.data.raw if coordinator.data and coordinator.data.raw else {}

        mac = raw.get("mac")
        connections = {(CONNECTION_NETWORK_MAC, format_mac(mac))} if mac else set()

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identity)},
            connections=connections,
            name=f"Luxsin ({host})",
            manufacturer="Luxsin",
            model=raw.get("device") or "X8/X9",
            sw_version=str(raw["version"]) if raw.get("version") is not None else None,
        )

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        if not self._parent_params:
            return True
        raw = self.coordinator.data.raw if self.coordinator.data else None
        if raw is None:
            return False
        return all(bool(raw.get(param)) for param in self._parent_params)


def entity_unique_id(entry: ConfigEntry, suffix: str) -> str:
    """Build a stable entity unique ID while preserving legacy IDs.

    Entries created before config-flow version 2 use their original host as
    the stored prefix. Reconfiguring such an entry to a new address therefore
    does not create replacement entities or break existing automations.
    """
    prefix = entry.data.get(CONF_ENTITY_ID_PREFIX, entry.data[CONF_HOST])
    return f"{DOMAIN}_{prefix}_{suffix}"


def has_fields(raw: dict | None, *fields: str) -> bool:
    """Whether ALL of the given fields are present in the last observed
    device status.

    Used by platforms (light/number/switch/select) so an entity is only
    created for capabilities the connected device's firmware actually
    reports, instead of hardcoding assumptions about which build has what.
    """
    if raw is None:
        return False
    return all(field in raw for field in fields)
