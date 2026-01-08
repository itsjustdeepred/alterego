
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .api import AlteregoAPI
from .const import DOMAIN
from .coordinator import AlteregoDataUpdateCoordinator

PLATFORMS = ["sensor", "climate", "select", "switch", "number", "time"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    
    api = AlteregoAPI(
        entry.data["username"],
        entry.data["password"],
    )

    coordinator = AlteregoDataUpdateCoordinator(
        hass,
        api,
        entry.data["station_id"],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator



    station_id = entry.data["station_id"]
    station_name = entry.data.get("station_name") or f"Alterego {station_id}"
    
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, station_id)},
        name=station_name,
        manufacturer="Alterego",
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.api.close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

