"""Coordinator behavior tests."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.luxsin.api import LuxsinError, LuxsinStatus
from custom_components.luxsin.coordinator import (
    FORCE_FULL_SYNC_EVERY,
    LuxsinCoordinator,
)


def _status(volume: int = 100) -> LuxsinStatus:
    return LuxsinStatus(volume=volume, raw={"volume": volume}, peq_profiles=[])


async def test_volume_is_published_before_device_write_finishes(hass) -> None:
    write_started = asyncio.Event()
    release_write = asyncio.Event()

    async def delayed_write(param: str, value: int) -> None:
        write_started.set()
        await release_write.wait()

    client = MagicMock()
    client.async_set_param = AsyncMock(side_effect=delayed_write)
    coordinator = LuxsinCoordinator(hass, client)
    coordinator.data = _status()
    listener = MagicMock()
    remove_listener = coordinator.async_add_listener(listener)

    task = asyncio.create_task(coordinator.async_apply_volume(150))
    await write_started.wait()

    assert coordinator.data.volume == 150
    assert coordinator.data.raw["volume"] == 150
    listener.assert_called_once()
    assert not task.done()

    release_write.set()
    await task
    remove_listener()


async def test_failed_volume_write_forces_next_full_sync(hass) -> None:
    client = MagicMock()
    client.async_set_param = AsyncMock(side_effect=LuxsinError("timeout"))
    client.async_get_msg_count = AsyncMock(return_value=1)
    client.async_get_full_status = AsyncMock(return_value=_status(100))
    coordinator = LuxsinCoordinator(hass, client)
    coordinator.data = _status()

    with pytest.raises(LuxsinError, match="timeout"):
        await coordinator.async_apply_volume(150)

    assert coordinator.data.volume == 150
    assert coordinator.data.raw["volume"] == 150
    assert coordinator._polls_since_full_sync == FORCE_FULL_SYNC_EVERY

    await coordinator.async_refresh()

    client.async_get_full_status.assert_awaited_once()
    assert coordinator.data.volume == 100
