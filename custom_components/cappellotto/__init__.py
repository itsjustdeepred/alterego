"""The Alterego integration."""

from __future__ import annotations

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AlteregoAPI
from .const import CONF_STATION_ID, CONF_STATION_NAME, DOMAIN, MANUFACTURER
from .coordinator import AlteregoConfigEntry, AlteregoDataUpdateCoordinator

PLATFORMS = [
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.TIME,
]


async def async_setup_entry(hass: HomeAssistant, entry: AlteregoConfigEntry) -> bool:
    """Set up an Alterego station from a config entry."""
    api = AlteregoAPI(
        async_get_clientsession(hass),
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    coordinator = AlteregoDataUpdateCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    station_id = entry.data[CONF_STATION_ID]
    station_device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, station_id)},
        name=entry.data.get(CONF_STATION_NAME) or f"Alterego {station_id}",
        manufacturer=MANUFACTURER,
        model="Station",
    )
    coordinator.station_device_id = station_device.id

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AlteregoConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
