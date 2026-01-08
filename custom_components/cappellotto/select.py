
from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEVICE_TYPE_DEUM,
    DEVICE_TYPE_ZONE,
    DOMAIN,
    FORCING_AUTO,
    FORCING_COMFORT,
    FORCING_ECONOMY,
    FORCING_OFF,
    OVERRIDE_AUTO,
    OVERRIDE_HIGH,
    OVERRIDE_LOW,
    OVERRIDE_MEDIUM,
    OVERRIDE_OFF,
    SEASON_SUMMER,
    SEASON_WINTER,
)
from .coordinator import AlteregoDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    
    coordinator: AlteregoDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []


    for zone in coordinator.data.get("zones", []):
        status = zone.get("status", {})
        if status.get("enabled") == 1:
            entities.append(AlteregoZoneForcingSelect(coordinator, zone))



    enabled_deums = []
    seen_ids = set()
    for deum in coordinator.data.get("deums", []):
        deum_id = deum.get("id")
        status = deum.get("status", {})
        

        if (deum_id and 
            status.get("enabled") == 1 and 
            status.get("user_visible") is True and
            deum_id not in seen_ids):
            seen_ids.add(deum_id)
            enabled_deums.append(deum)
    

    for deum in enabled_deums:
        entities.append(AlteregoDeumOverrideSelect(coordinator, deum))


    for timer in coordinator.data.get("timers", []):
        status = timer.get("status", {})
        if status.get("enabled") == 1:
            params = timer.get("params", {})
            

            days = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
            max_slots = 6
            

            existing_slots = set()
            for key in params.keys():
                if key.startswith("S_") and len(key.split("_")) >= 3:
                    existing_slots.add(key)
            

            for day in days:
                for slot_num in range(max_slots):
                    slot_key = f"S_{day}_{slot_num}"

                    entities.append(AlteregoTimerSlotSelect(coordinator, timer, slot_key))


    if coordinator.data.get("global"):
        entities.append(AlteregoSeasonSelect(coordinator))

    async_add_entities(entities)


class AlteregoZoneForcingSelect(CoordinatorEntity, SelectEntity):
    

    _attr_options = [FORCING_AUTO, FORCING_COMFORT, FORCING_ECONOMY, FORCING_OFF]
    _attr_icon = "mdi:thermostat"

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
        zone_data: dict[str, Any],
    ) -> None:
        
        super().__init__(coordinator)
        self._zone_id = zone_data.get("id")
        self._zone_data = zone_data
        self._station_id = coordinator.station_id
        status = zone_data.get("status", {})
        self._zone_name = status.get("description", f"Zone {self._zone_id}")
        self._attr_name = f"{self._zone_name} Mode"
        self._attr_unique_id = f"{self._station_id}_{self._zone_id}_forcing"

    @property
    def device_info(self) -> dict[str, Any]:
        
        return {
            "identifiers": {(DOMAIN, f"{self._station_id}_{self._zone_id}")},
            "name": self._zone_name,
            "manufacturer": "Alterego",
            "model": DEVICE_TYPE_ZONE,
            "via_device": (DOMAIN, self._station_id),
        }

    @property
    def current_option(self) -> str:
        
        zone = self._get_zone_data()
        return zone.get("params", {}).get("forcing", FORCING_AUTO)

    def _get_zone_data(self) -> dict[str, Any]:
        
        zones = self.coordinator.data.get("zones", [])
        for zone in zones:
            if zone.get("id") == self._zone_id:
                return zone
        return self._zone_data

    async def async_select_option(self, option: str) -> None:
        
        await self.coordinator.api.update_zone(
            self._station_id,
            self._zone_id,
            {"forcing": option},
        )
        await self.coordinator.async_request_refresh()


class AlteregoDeumOverrideSelect(CoordinatorEntity, SelectEntity):
    

    _attr_options = [OVERRIDE_AUTO, OVERRIDE_LOW, OVERRIDE_MEDIUM, OVERRIDE_HIGH, OVERRIDE_OFF]
    _attr_icon = "mdi:air-humidifier"

    @property
    def available(self) -> bool:
        
        return True

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
        deum_data: dict[str, Any],
    ) -> None:
        
        super().__init__(coordinator)
        self._deum_id = deum_data.get("id")
        self._deum_data = deum_data
        self._station_id = coordinator.station_id
        status = deum_data.get("status", {})

        description = status.get("description", "").strip()
        if description:
            self._deum_name = description
        else:
            self._deum_name = f"Deumidificatore {self._deum_id}"
        self._attr_name = f"{self._deum_name} Override"
        self._attr_unique_id = f"{self._station_id}_{self._deum_id}_override"

    @property
    def device_info(self) -> dict[str, Any]:
        
        return {
            "identifiers": {(DOMAIN, f"{self._station_id}_{self._deum_id}")},
            "name": f"{self._deum_name} {self._deum_id}",
            "manufacturer": "Alterego",
            "model": DEVICE_TYPE_DEUM,
            "via_device": (DOMAIN, self._station_id),
        }

    @property
    def current_option(self) -> str:
        
        deum = self._get_deum_data()
        return deum.get("params", {}).get("user_override", OVERRIDE_AUTO)

    def _get_deum_data(self) -> dict[str, Any]:
        
        deums = self.coordinator.data.get("deums", [])
        for deum in deums:
            if deum.get("id") == self._deum_id:
                return deum
        return self._deum_data

    async def async_select_option(self, option: str) -> None:
        
        await self.coordinator.api.update_deum(
            self._station_id,
            self._deum_id,
            {"user_override": option},
        )
        await self.coordinator.async_request_refresh()


class AlteregoSeasonSelect(CoordinatorEntity, SelectEntity):
    

    _attr_options = [SEASON_WINTER, SEASON_SUMMER]
    _attr_icon = "mdi:weather-snowy-rainy"
    _attr_name = "Season"
    _attr_unique_id = None

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
    ) -> None:
        
        super().__init__(coordinator)
        self._station_id = coordinator.station_id
        self._attr_unique_id = f"{self._station_id}_season"

    @property
    def device_info(self) -> dict[str, Any]:
        
        return {
            "identifiers": {(DOMAIN, self._station_id)},
            "name": f"Alterego {self._station_id}",
            "manufacturer": "Alterego",
        }

    @property
    def current_option(self) -> str:
        
        global_data = self.coordinator.data.get("global", {})
        return global_data.get("params", {}).get("global_set_season", SEASON_WINTER)

    async def async_select_option(self, option: str) -> None:
        
        await self.coordinator.api.update_global(
            self._station_id,
            {"global_set_season": option},
        )
        await self.coordinator.async_request_refresh()


class AlteregoTimerSlotSelect(CoordinatorEntity, SelectEntity):
    

    _attr_icon = "mdi:timer"
    _attr_options = ["COMFORT", "ECONOMY", "OFF", "N/U"]

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
            slot_num = parts[2]

            self._attr_name = f"{self._timer_name} {day}"
            self._slot_number = slot_num
        else:
            self._attr_name = f"{self._timer_name} {slot_key}"
            self._slot_number = "0"
        
        self._attr_unique_id = f"{self._station_id}_{self._timer_id}_{slot_key}"

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
    def current_option(self) -> str:
        
        timer = self._get_timer_data()
        params = timer.get("params", {})
        value = params.get(self._slot_key, "N/U")
        if value == "N/U":
            return "N/U"

        if " " in value:
            return value.split()[0]
        return value

    def _get_timer_data(self) -> dict[str, Any]:
        
        timers = self.coordinator.data.get("timers", [])
        for timer in timers:
            if timer.get("id") == self._timer_id:
                return timer
        return self._timer_data

    async def async_select_option(self, option: str) -> None:
        
        timer = self._get_timer_data()
        params = timer.get("params", {})
        current_value = params.get(self._slot_key, "N/U")
        

        if " " in current_value and current_value != "N/U":
            time_part = current_value.split()[1] if len(current_value.split()) > 1 else "00:00"
            new_value = f"{option} {time_part}"
        elif option == "N/U":
            new_value = "N/U"
        else:

            new_value = f"{option} 00:00"
        
        await self.coordinator.api.update_timer(
            self._station_id,
            self._timer_id,
            {self._slot_key: new_value},
        )

        await self.coordinator.async_request_refresh()

