"""Waktu Solat Malaysia integration using solat.my API."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_NAME, CONF_ZONE, DEFAULT_NAME, DEFAULT_ZONE, DOMAIN
from .coordinator import SolatMyCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.TEXT,
]

MIMBAR_FRONTEND_URL = f"/api/{DOMAIN}/mimbar"
MIMBAR_FRONTEND_PATH = Path(__file__).parent / "frontend"
MIMBAR_FRONTEND_REGISTERED = f"{DOMAIN}_mimbar_frontend_registered"
MIMBAR_FRONTEND_LOCK = f"{DOMAIN}_mimbar_frontend_lock"


async def _async_register_mimbar_frontend(hass: HomeAssistant) -> None:
    """Register the Mimbar card module directory once for this process."""
    lock = hass.data.setdefault(MIMBAR_FRONTEND_LOCK, asyncio.Lock())
    async with lock:
        if hass.data.get(MIMBAR_FRONTEND_REGISTERED):
            return

        await hass.http.async_register_static_paths(
            [StaticPathConfig(MIMBAR_FRONTEND_URL, str(MIMBAR_FRONTEND_PATH), False)]
        )
        hass.data[MIMBAR_FRONTEND_REGISTERED] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waktu Solat Malaysia from a config entry."""
    await _async_register_mimbar_frontend(hass)

    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    zone = entry.data.get(CONF_ZONE, DEFAULT_ZONE)

    coordinator = SolatMyCoordinator(hass, name=name, initial_zone=zone)
    await coordinator.async_config_entry_first_refresh()
    coordinator.async_setup()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: SolatMyCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator.async_shutdown()
    return unload_ok
