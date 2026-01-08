
from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEVICE_TYPE_ZONE,
    DOMAIN,
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
        if status.get("enabled") != 1:
            continue

        zone_id = zone.get("id")
        params = zone.get("params", {})
        zone_type = status.get("type", "")


        if params.get("setpoint_comfort_summer"):
            entities.append(
                AlteregoSetpointNumber(
                    coordinator, zone_id, zone, "setpoint_comfort_summer", "Summer Comfort"
                )
            )


        if params.get("setpoint_economy_summer"):
            entities.append(
                AlteregoSetpointNumber(
                    coordinator, zone_id, zone, "setpoint_economy_summer", "Summer Economy"
                )
            )


        if params.get("setpoint_comfort_winter"):
            entities.append(
                AlteregoSetpointNumber(
                    coordinator, zone_id, zone, "setpoint_comfort_winter", "Winter Comfort"
                )
            )


        if params.get("setpoint_economy_winter"):
            entities.append(
                AlteregoSetpointNumber(
                    coordinator, zone_id, zone, "setpoint_economy_winter", "Winter Economy"
                )
            )


        if "RH" in zone_type and params.get("setpoint_humidity") is not None:
            entities.append(
                AlteregoHumiditySetpointNumber(coordinator, zone_id, zone)
            )



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
        deum_id = deum.get("id")
        entities.append(
            AlteregoDeumBoostTimerNumber(coordinator, deum_id, deum)
        )

    async_add_entities(entities)


class AlteregoSetpointNumber(CoordinatorEntity, NumberEntity):
    

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 10.0
    _attr_native_max_value = 30.0
    _attr_native_step = 0.5

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
        zone_id: str,
        zone_data: dict[str, Any],
        setpoint_key: str,
        setpoint_name: str,
    ) -> None:
        
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._zone_data = zone_data
        self._station_id = coordinator.station_id
        self._setpoint_key = setpoint_key
        status = zone_data.get("status", {})
        self._zone_name = status.get("description", f"Zone {zone_id}")
        self._attr_name = f"{self._zone_name} {setpoint_name} Setpoint"
        self._attr_unique_id = f"{self._station_id}_{zone_id}_{setpoint_key}"

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
    def native_value(self) -> float | None:
        
        zone = self._get_zone_data()
        params = zone.get("params", {})
        value = params.get(self._setpoint_key)
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _get_zone_data(self) -> dict[str, Any]:
        
        zones = self.coordinator.data.get("zones", [])
        for zone in zones:
            if zone.get("id") == self._zone_id:
                return zone
        return self._zone_data

    async def async_set_native_value(self, value: float) -> None:
        
        await self.coordinator.api.update_zone(
            self._station_id,
            self._zone_id,
            {self._setpoint_key: value},
        )
        await self.coordinator.async_request_refresh()


class AlteregoHumiditySetpointNumber(CoordinatorEntity, NumberEntity):
    

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 30.0
    _attr_native_max_value = 80.0
    _attr_native_step = 0.5

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
        zone_id: str,
        zone_data: dict[str, Any],
    ) -> None:
        
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._zone_data = zone_data
        self._station_id = coordinator.station_id
        status = zone_data.get("status", {})
        self._zone_name = status.get("description", f"Zone {zone_id}")
        self._attr_name = f"{self._zone_name} Humidity Setpoint"
        self._attr_unique_id = f"{self._station_id}_{zone_id}_setpoint_humidity"

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
    def native_value(self) -> float | None:
        
        zone = self._get_zone_data()
        params = zone.get("params", {})
        value = params.get("setpoint_humidity")
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @property
    def available(self) -> bool:
        
        global_data = self.coordinator.data.get("global", {})
        season = global_data.get("status", {}).get("global_season", SEASON_WINTER)
        return season == SEASON_SUMMER

    def _get_zone_data(self) -> dict[str, Any]:
        
        zones = self.coordinator.data.get("zones", [])
        for zone in zones:
            if zone.get("id") == self._zone_id:
                return zone
        return self._zone_data

    async def async_set_native_value(self, value: float) -> None:
        

        global_data = self.coordinator.data.get("global", {})
        season = global_data.get("status", {}).get("global_season", SEASON_WINTER)
        if season != SEASON_SUMMER:
            from homeassistant.exceptions import HomeAssistantError
            raise HomeAssistantError("Humidity setpoint can only be modified in summer mode")

        await self.coordinator.api.update_zone(
            self._station_id,
            self._zone_id,
            {"setpoint_humidity": value},
        )
        await self.coordinator.async_request_refresh()


class AlteregoDeumBoostTimerNumber(CoordinatorEntity, NumberEntity):
    

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_icon = "mdi:timer"

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
        deum_id: str,
        deum_data: dict[str, Any],
    ) -> None:
        
        super().__init__(coordinator)
        self._deum_id = deum_id
        self._deum_data = deum_data
        self._station_id = coordinator.station_id
        status = deum_data.get("status", {})

        description = status.get("description", "").strip()
        if description:
            self._deum_name = description
        else:
            self._deum_name = f"Deumidificatore {deum_id}"
        self._attr_name = f"{self._deum_name} Boost Timer"
        self._attr_unique_id = f"{self._station_id}_{deum_id}_boost_timer"

    @property
    def device_info(self) -> dict[str, Any]:
        
        return {
            "identifiers": {(DOMAIN, f"{self._station_id}_{self._deum_id}")},
            "name": f"{self._deum_name} {self._deum_id}",
            "manufacturer": "Alterego",
            "model": "Deumidificatore",
            "via_device": (DOMAIN, self._station_id),
        }

    @property
    def native_value(self) -> float | None:
        
        deum = self._get_deum_data()
        params = deum.get("params", {})
        value = params.get("boost_timer")
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @property
    def available(self) -> bool:
        
        global_data = self.coordinator.data.get("global", {})
        season = global_data.get("status", {}).get("global_season", SEASON_WINTER)
        return season == SEASON_SUMMER

    def _get_deum_data(self) -> dict[str, Any]:
        
        deums = self.coordinator.data.get("deums", [])
        for deum in deums:
            if deum.get("id") == self._deum_id:
                return deum
        return self._deum_data

    async def async_set_native_value(self, value: float) -> None:
        

        global_data = self.coordinator.data.get("global", {})
        season = global_data.get("status", {}).get("global_season", SEASON_WINTER)
        if season != SEASON_SUMMER:
            from homeassistant.exceptions import HomeAssistantError
            raise HomeAssistantError("Boost timer can only be modified in summer mode")

        deum = self._get_deum_data()
        params = deum.get("params", {})
        
        await self.coordinator.api.update_deum(
            self._station_id,
            self._deum_id,
            {
                "boost_timer": int(value),
                "vent_speed_boost": params.get("vent_speed_boost", 80),
                "vent_speed_comfort": params.get("vent_speed_comfort", 40),
                "vent_speed_economy": params.get("vent_speed_economy", 0),
            },
        )
        await self.coordinator.async_request_refresh()

