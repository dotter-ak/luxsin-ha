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

from .const import DOMAIN
from .coordinator import LuxsinCoordinator


class LuxsinEntity(CoordinatorEntity[LuxsinCoordinator]):
    """Base class providing a shared DeviceInfo built from the latest raw status."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: LuxsinCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        host = entry.data[CONF_HOST]
        raw = coordinator.data.raw if coordinator.data and coordinator.data.raw else {}

        mac = raw.get("mac")
        connections = {(CONNECTION_NETWORK_MAC, format_mac(mac))} if mac else set()

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host)},
            connections=connections,
            name=f"Luxsin ({host})",
            manufacturer="Luxsin",
            model=raw.get("device") or "X8/X9",
            sw_version=str(raw["version"]) if raw.get("version") is not None else None,
        )


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
