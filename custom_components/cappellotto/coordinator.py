"""Data update coordinator for the Alterego integration."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AlteregoAPI, AlteregoAPIError, AlteregoAuthenticationError
from .const import (
    CONF_STATION_ID,
    DOMAIN,
    RESOURCE_DEUMS,
    RESOURCE_GLOBAL,
    RESOURCE_TIMERS,
    RESOURCE_ZONES,
    SCAN_INTERVAL,
    SEASON_WINTER,
    TIMER_DAYS,
    TIMER_SLOT_UNUSED,
    TIMER_SLOTS_PER_DAY,
    UPDATE_INTERVALS,
)

_LOGGER = logging.getLogger(__name__)

type AlteregoConfigEntry = ConfigEntry[AlteregoDataUpdateCoordinator]

# A failure on these makes the whole update fail (entities become unavailable).
_REQUIRED_RESOURCES = (RESOURCE_ZONES, RESOURCE_GLOBAL)
# A failure on these keeps the last known data and is retried on the next tick.
_OPTIONAL_RESOURCES = (RESOURCE_DEUMS, RESOURCE_TIMERS)


class AlteregoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls one Alterego station, each resource at its own pace."""

    config_entry: AlteregoConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: AlteregoConfigEntry,
        api: AlteregoAPI,
    ) -> None:
        self.api = api
        self.station_id: str = entry.data[CONF_STATION_ID]
        # Registry id of the station device, set during setup.
        self.station_device_id = ""
        self._last_fetch: dict[str, float] = {}
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"Alterego {self.station_id}",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    def _is_due(self, resource: str) -> bool:
        last = self._last_fetch.get(resource)
        return last is None or time.monotonic() - last >= UPDATE_INTERVALS[resource]

    async def _fetch(self, resource: str) -> Any:
        payload = await self.api.get_resource(self.station_id, resource)
        if resource == RESOURCE_GLOBAL:
            if not isinstance(payload, dict):
                raise AlteregoAPIError(f"Unexpected {resource} payload")
            payload = payload.get("data") or {}
        elif not isinstance(payload, list):
            raise AlteregoAPIError(f"Unexpected {resource} payload")
        return payload

    async def _async_update_data(self) -> dict[str, Any]:
        previous = self.data or {}
        data: dict[str, Any] = {}
        # Only remembered if the whole update succeeds, otherwise data is dropped.
        fetched: dict[str, float] = {}

        try:
            for resource in _REQUIRED_RESOURCES:
                if resource in previous and not self._is_due(resource):
                    data[resource] = previous[resource]
                else:
                    data[resource] = await self._fetch(resource)
                    fetched[resource] = time.monotonic()

            for resource in _OPTIONAL_RESOURCES:
                if resource in previous and not self._is_due(resource):
                    data[resource] = previous[resource]
                    continue
                try:
                    data[resource] = await self._fetch(resource)
                    fetched[resource] = time.monotonic()
                except AlteregoAuthenticationError:
                    raise
                except AlteregoAPIError as err:
                    _LOGGER.warning("Failed to update %s: %s", resource, err)
                    data[resource] = previous.get(resource, [])
        except AlteregoAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except AlteregoAPIError as err:
            raise UpdateFailed(
                f"Error communicating with the Alterego API: {err}"
            ) from err

        self._last_fetch.update(fetched)
        return data

    async def async_write(
        self, resource: str, data: dict[str, Any], item_id: str | None = None
    ) -> None:
        """Send a change to the API, then re-read the affected resource."""
        try:
            if resource == RESOURCE_GLOBAL:
                await self.api.update_global(self.station_id, data)
            else:
                assert item_id is not None
                await self.api.update_item(self.station_id, resource, item_id, data)
        except AlteregoAPIError as err:
            if isinstance(err, AlteregoAuthenticationError):
                self.config_entry.async_start_reauth(self.hass)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={"error": str(err)},
            ) from err

        # Without this the slower resources would show the old value for minutes.
        self._last_fetch.pop(resource, None)
        await self.async_request_refresh()

    @property
    def season(self) -> str:
        """Season the station is currently running in (SUMMER / WINTER)."""
        return (
            self.data[RESOURCE_GLOBAL]
            .get("status", {})
            .get("global_season", SEASON_WINTER)
        )

    @property
    def global_params(self) -> dict[str, Any]:
        return self.data[RESOURCE_GLOBAL].get("params", {})

    def get_item(self, resource: str, item_id: str) -> dict[str, Any] | None:
        """Return the zone, deum or timer with the given id, if present."""
        for item in self.data.get(resource, []):
            if item.get("id") == item_id:
                return item
        return None

    def enabled_zones(self) -> Iterator[dict[str, Any]]:
        for zone in self.data[RESOURCE_ZONES]:
            if zone.get("id") and zone.get("status", {}).get("enabled") == 1:
                yield zone

    def visible_deums(self) -> Iterator[dict[str, Any]]:
        """Enabled, user-visible dehumidifiers; the API may list one twice."""
        seen: set[str] = set()
        for deum in self.data[RESOURCE_DEUMS]:
            deum_id = deum.get("id")
            status = deum.get("status", {})
            if (
                deum_id
                and deum_id not in seen
                and status.get("enabled") == 1
                and status.get("user_visible") is True
            ):
                seen.add(deum_id)
                yield deum

    def active_timer_slots(self) -> Iterator[tuple[dict[str, Any], str]]:
        """(timer, slot_key) for every used slot of every enabled timer."""
        for timer in self.data[RESOURCE_TIMERS]:
            if not timer.get("id") or timer.get("status", {}).get("enabled") != 1:
                continue
            params = timer.get("params", {})
            for day in TIMER_DAYS:
                for slot in range(TIMER_SLOTS_PER_DAY):
                    slot_key = f"S_{day}_{slot}"
                    if params.get(slot_key, TIMER_SLOT_UNUSED) != TIMER_SLOT_UNUSED:
                        yield timer, slot_key
