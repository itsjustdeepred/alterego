
from datetime import timedelta
import logging
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AlteregoAPI, AlteregoAPIError
from .const import (
    UPDATE_INTERVAL_ZONES,
    UPDATE_INTERVAL_GLOBAL,
    UPDATE_INTERVAL_DEUMS,
    UPDATE_INTERVAL_TIMERS,
    SAFE_REFRESH_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class AlteregoDataUpdateCoordinator(DataUpdateCoordinator):
    

    def __init__(
        self,
        hass: HomeAssistant,
        api: AlteregoAPI,
        station_id: str,
    ) -> None:
        
        self.api = api
        self.station_id = station_id
        

        initial_data: Dict[str, Any] = {
            "zones": [],
            "global": {},
            "deums": [],
            "timers": [],
        }

        super().__init__(
            hass,
            _LOGGER,
            name=f"Alterego {station_id}",
            update_interval=timedelta(seconds=SAFE_REFRESH_INTERVAL),
        )
        

        if self.data is None:
            self.data = initial_data

    async def _async_update_data(self) -> Dict[str, Any]:
        

        data: Dict[str, Any] = {
            "zones": [],
            "global": {},
            "deums": [],
            "timers": [],
        }

        try:

            try:
                zones = await self.api.get_zones(self.station_id)
                if zones is not None and isinstance(zones, list):
                    data["zones"] = zones
            except AlteregoAPIError as err:
                _LOGGER.warning("Failed to update zones: %s", err)


            current_time = self.hass.loop.time()
            if not hasattr(self, "_last_global_update") or \
               (current_time - getattr(self, "_last_global_update", 0)) > UPDATE_INTERVAL_GLOBAL:
                try:
                    global_data = await self.api.get_global_status(self.station_id)
                    if global_data is not None:
                        data["global"] = global_data.get("data", {}) or {}
                    self._last_global_update = current_time
                except AlteregoAPIError as err:
                    _LOGGER.warning("Failed to update global status: %s", err)

                    if self.data and "global" in self.data:
                        data["global"] = self.data["global"]


            if not hasattr(self, "_last_deums_update") or \
               (current_time - getattr(self, "_last_deums_update", 0)) > UPDATE_INTERVAL_DEUMS:
                try:
                    deums = await self.api.get_deums(self.station_id)
                    if deums is not None and isinstance(deums, list):
                        data["deums"] = deums
                    self._last_deums_update = current_time
                except AlteregoAPIError as err:
                    _LOGGER.warning("Failed to update deums: %s", err)

                    if self.data and "deums" in self.data:
                        data["deums"] = self.data["deums"]


            if not hasattr(self, "_last_timers_update") or \
               (current_time - getattr(self, "_last_timers_update", 0)) > UPDATE_INTERVAL_TIMERS:
                try:
                    timers = await self.api.get_timers(self.station_id)
                    if timers is not None and isinstance(timers, list):
                        data["timers"] = timers
                    self._last_timers_update = current_time
                except AlteregoAPIError as err:
                    _LOGGER.warning("Failed to update timers: %s", err)

                    if self.data and "timers" in self.data:
                        data["timers"] = self.data["timers"]

            return data

        except AlteregoAPIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

