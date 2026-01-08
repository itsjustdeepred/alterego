
from __future__ import annotations

from typing import Any
from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AlteregoDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    
    coordinator: AlteregoDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []



    for timer in coordinator.data.get("timers", []):
        status = timer.get("status", {})
        if status.get("enabled") == 1:

            days = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
            max_slots = 6
            

            for day in days:
                for slot_num in range(max_slots):
                    slot_key = f"S_{day}_{slot_num}"
                    entities.append(AlteregoTimerSlotTime(coordinator, timer, slot_key))

    async_add_entities(entities)


class AlteregoTimerSlotTime(CoordinatorEntity, TimeEntity):
    

    _attr_icon = "mdi:clock-time-four"

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
        timer_data: dict[str, Any],
        slot_key: str,
    ) -> None:
        
        super().__init__(coordinator)
        self._timer_id = timer_data.get("id")
        self._timer_data = timer_data
        self._slot_key = slot_key
        self._station_id = coordinator.station_id
        status = timer_data.get("status", {})
        self._timer_name = status.get("description", f"Timer {self._timer_id}")
        

        day_map = {
            "MO": "Lunedì", "TU": "Martedì", "WE": "Mercoledì", "TH": "Giovedì",
            "FR": "Venerdì", "SA": "Sabato", "SU": "Domenica"
        }
        day_map_en = {
            "MO": "Monday", "TU": "Tuesday", "WE": "Wednesday", "TH": "Thursday",
            "FR": "Friday", "SA": "Saturday", "SU": "Sunday"
        }
        parts = slot_key.split("_")
        if len(parts) >= 3:
            day_code = parts[1]
            day = day_map.get(day_code, day_map_en.get(day_code, day_code))

            self._attr_name = f"{self._timer_name} {day}"
        else:
            self._attr_name = f"{self._timer_name} {slot_key}"
        
        self._attr_unique_id = f"{self._station_id}_{self._timer_id}_{slot_key}_time"

    @property
    def device_info(self) -> dict[str, Any]:
        
        return {
            "identifiers": {(DOMAIN, f"{self._station_id}_{self._timer_id}")},
            "name": self._timer_name,
            "manufacturer": "Alterego",
            "model": "Timer",
            "via_device": (DOMAIN, self._station_id),
        }

    @property
    def native_value(self) -> time | None:
        
        timer = self._get_timer_data()
        params = timer.get("params", {})
        value = params.get(self._slot_key, "N/U")
        if value == "N/U" or " " not in value:
            return None
        

        time_str = value.split()[1] if len(value.split()) > 1 else None
        if not time_str:
            return None
        
        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        except (ValueError, TypeError):
            return None

    @property
    def available(self) -> bool:
        
        timer = self._get_timer_data()
        params = timer.get("params", {})
        value = params.get(self._slot_key, "N/U")
        return value != "N/U" and " " in value

    def _get_timer_data(self) -> dict[str, Any]:
        
        timers = self.coordinator.data.get("timers", [])
        for timer in timers:
            if timer.get("id") == self._timer_id:
                return timer
        return self._timer_data

    async def async_set_value(self, value: time) -> None:
        
        timer = self._get_timer_data()
        params = timer.get("params", {})
        current_value = params.get(self._slot_key, "N/U")
        

        if " " in current_value and current_value != "N/U":
            mode = current_value.split()[0]
        else:
            mode = "COMFORT"
        
        time_str = value.strftime("%H:%M")
        new_value = f"{mode} {time_str}"
        
        await self.coordinator.api.update_timer(
            self._station_id,
            self._timer_id,
            {self._slot_key: new_value},
        )
        await self.coordinator.async_request_refresh()

