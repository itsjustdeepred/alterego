
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEVICE_TYPE_ZONE,
    DOMAIN,
    FORCING_AUTO,
    FORCING_COMFORT,
    FORCING_ECONOMY,
    FORCING_OFF,
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
            entities.append(AlteregoClimate(coordinator, zone))

    async_add_entities(entities)


class AlteregoClimate(CoordinatorEntity, ClimateEntity):
    

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_preset_modes = [FORCING_AUTO, FORCING_COMFORT, FORCING_ECONOMY, FORCING_OFF]

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
        self._attr_name = self._zone_name
        self._attr_unique_id = f"{self._station_id}_{self._zone_id}_climate"

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
    def current_temperature(self) -> float | None:
        
        zone = self._get_zone_data()
        status = zone.get("status", {})
        temp = status.get("temperature")
        if temp in [None, "N/A", "N/C"]:
            return None
        try:
            return float(temp)
        except (ValueError, TypeError):
            return None

    @property
    def target_temperature(self) -> float | None:
        
        zone = self._get_zone_data()
        status = zone.get("status", {})
        setpoint = status.get("current_setpoint")
        if setpoint in [None, "N/A", "0.0"]:
            return None
        try:
            return float(setpoint)
        except (ValueError, TypeError):
            return None

    @property
    def hvac_mode(self) -> HVACMode:
        
        zone = self._get_zone_data()
        status = zone.get("status", {})
        forcing = zone.get("params", {}).get("forcing", FORCING_AUTO)
        output = status.get("zone_output", "OFF")

        if forcing == FORCING_OFF or output == "OFF":
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def preset_mode(self) -> str:
        
        zone = self._get_zone_data()
        forcing = zone.get("params", {}).get("forcing", FORCING_AUTO)
        return forcing

    @property
    def min_temp(self) -> float:
        
        zone = self._get_zone_data()
        params = zone.get("params", {})
        global_data = self.coordinator.data.get("global", {})
        global_params = global_data.get("params", {})


        season = global_data.get("status", {}).get("global_season", "WINTER")
        
        if season == "SUMMER":
            min_temp = global_params.get("global_zset_min_summer", "15.0")
        else:
            min_temp = global_params.get("global_zset_min_winter", "10.0")

        try:
            return float(min_temp)
        except (ValueError, TypeError):
            return 10.0

    @property
    def max_temp(self) -> float:
        
        zone = self._get_zone_data()
        global_data = self.coordinator.data.get("global", {})
        global_params = global_data.get("params", {})


        season = global_data.get("status", {}).get("global_season", "WINTER")
        
        if season == "SUMMER":
            max_temp = global_params.get("global_zset_max_summer", "30.0")
        else:
            max_temp = global_params.get("global_zset_max_winter", "30.0")

        try:
            return float(max_temp)
        except (ValueError, TypeError):
            return 30.0

    def _get_zone_data(self) -> dict[str, Any]:
        
        zones = self.coordinator.data.get("zones", [])
        for zone in zones:
            if zone.get("id") == self._zone_id:
                return zone
        return self._zone_data

    async def async_set_temperature(self, **kwargs: Any) -> None:
        
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        zone = self._get_zone_data()
        params = zone.get("params", {})
        global_data = self.coordinator.data.get("global", {})
        season = global_data.get("status", {}).get("global_season", "WINTER")


        forcing = params.get("forcing", FORCING_AUTO)
        update_data = {}

        if forcing == FORCING_COMFORT:
            if season == "SUMMER":
                update_data["setpoint_comfort_summer"] = temperature
            else:
                update_data["setpoint_comfort_winter"] = temperature
        elif forcing == FORCING_ECONOMY:
            if season == "SUMMER":
                update_data["setpoint_economy_summer"] = temperature
            else:
                update_data["setpoint_economy_winter"] = temperature
        else:

            if season == "SUMMER":
                update_data["setpoint_comfort_summer"] = temperature
            else:
                update_data["setpoint_comfort_winter"] = temperature

        await self.coordinator.api.update_zone(
            self._station_id,
            self._zone_id,
            update_data,
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        
        if hvac_mode == HVACMode.OFF:
            await self.async_set_preset_mode(FORCING_OFF)
        else:
            await self.async_set_preset_mode(FORCING_AUTO)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        
        await self.coordinator.api.update_zone(
            self._station_id,
            self._zone_id,
            {"forcing": preset_mode},
        )
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        
        zone = self._get_zone_data()
        status = zone.get("status", {})
        params = zone.get("params", {})
        return {
            "zone_id": self._zone_id,
            "zone_type": status.get("type"),
            "current_mode": status.get("current_mode"),
            "zone_output": status.get("zone_output"),
            "setpoint_comfort_summer": params.get("setpoint_comfort_summer"),
            "setpoint_comfort_winter": params.get("setpoint_comfort_winter"),
            "setpoint_economy_summer": params.get("setpoint_economy_summer"),
            "setpoint_economy_winter": params.get("setpoint_economy_winter"),
        }

