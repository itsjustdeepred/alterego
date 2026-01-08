
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DEWPOINT,
    ATTR_HUMIDITY,
    ATTR_TEMPERATURE,
    ATTR_ZONE_ID,
    DEVICE_TYPE_ZONE,
    DOMAIN,
)
from .coordinator import AlteregoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class AlteregoGlobalSensor(CoordinatorEntity, SensorEntity):
    

    _attr_icon = "mdi:home-thermometer"

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
    ) -> None:
        
        super().__init__(coordinator)
        self._station_id = coordinator.station_id
        self._attr_name = f"Alterego {self._station_id} Status"
        self._attr_unique_id = f"{self._station_id}_global_status"

    @property
    def device_info(self) -> dict[str, Any]:
        
        return {
            "identifiers": {(DOMAIN, self._station_id)},
            "name": f"Alterego {self._station_id}",
            "manufacturer": "Alterego",
        }

    @property
    def native_value(self) -> str:
        
        global_data = self.coordinator.data.get("global", {})
        status = global_data.get("status", {})
        return status.get("global_status", "UNKNOWN")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        
        global_data = self.coordinator.data.get("global", {})
        status = global_data.get("status", {})
        params = global_data.get("params", {})
        outside_temp = status.get("outside_temp")

        outside_temp_value = None
        if outside_temp not in [None, "N/A", "N/C", ""]:
            try:
                outside_temp_value = float(outside_temp)
            except (ValueError, TypeError):
                pass
        
        return {
            "season": status.get("global_season"),
            "outside_temperature": outside_temp_value,
            "last_connection": status.get("last_connection"),
            "global_enable": params.get("global_enable"),
        }


class AlteregoOutsideTemperatureSensor(CoordinatorEntity, SensorEntity):
    

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:thermometer"

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
    ) -> None:
        
        super().__init__(coordinator)
        self._station_id = coordinator.station_id
        self._attr_name = f"Alterego {self._station_id} Outside Temperature"
        self._attr_unique_id = f"{self._station_id}_outside_temperature"

    @property
    def device_info(self) -> dict[str, Any]:
        
        return {
            "identifiers": {(DOMAIN, self._station_id)},
            "name": f"Alterego {self._station_id}",
            "manufacturer": "Alterego",
        }

    @property
    def native_value(self) -> float | None:
        
        global_data = self.coordinator.data.get("global", {})
        status = global_data.get("status", {})
        outside_temp = status.get("outside_temp")
        
        if outside_temp in [None, "N/A", "N/C", ""]:
            return None
        
        try:
            return float(outside_temp)
        except (ValueError, TypeError):
            return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    
    coordinator: AlteregoDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []


    if coordinator.data.get("global"):
        entities.append(AlteregoGlobalSensor(coordinator))

        entities.append(AlteregoOutsideTemperatureSensor(coordinator))


    for zone in coordinator.data.get("zones", []):
        zone_id = zone.get("id")
        status = zone.get("status", {})
        zone_type = status.get("type", "")
        

        if status.get("enabled") != 1:
            continue


        if status.get("temperature") not in [None, "N/A", "N/C"]:
            entities.append(
                AlteregoTemperatureSensor(coordinator, zone_id, zone)
            )




        if "RH" in zone_type:
            humidity = status.get("humidity")

            if humidity and humidity not in ["N/C", "N/A", "", None]:
                _LOGGER.debug(
                    "Creating humidity sensor for zone %s (type: %s, humidity: %s)",
                    zone_id,
                    zone_type,
                    humidity,
                )
                entities.append(
                    AlteregoHumiditySensor(coordinator, zone_id, zone)
                )
            else:
                _LOGGER.debug(
                    "Skipping humidity sensor for zone %s (type: %s, humidity: %s)",
                    zone_id,
                    zone_type,
                    humidity,
                )



        if "RH" in zone_type:
            dewpoint = status.get("dewpoint")

            if dewpoint and dewpoint not in ["N/C", "N/A", "", None]:
                _LOGGER.debug(
                    "Creating dewpoint sensor for zone %s (type: %s, dewpoint: %s)",
                    zone_id,
                    zone_type,
                    dewpoint,
                )
                entities.append(
                    AlteregoDewpointSensor(coordinator, zone_id, zone)
                )
            else:
                _LOGGER.debug(
                    "Skipping dewpoint sensor for zone %s (type: %s, dewpoint: %s)",
                    zone_id,
                    zone_type,
                    dewpoint,
                )

    async_add_entities(entities)


class AlteregoSensorBase(CoordinatorEntity, SensorEntity):
    

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
        self._sensor_key = "sensor"

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
    def unique_id(self) -> str:
        
        return f"{self._station_id}_{self._zone_id}_{self._sensor_key}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        
        zone = self._get_zone_data()
        status = zone.get("status", {})
        return {
            ATTR_ZONE_ID: self._zone_id,
            "zone_name": self._zone_name,
            "zone_type": status.get("type"),
            "enabled": status.get("enabled"),
            "current_mode": status.get("current_mode"),
            "zone_output": status.get("zone_output"),
        }

    def _get_zone_data(self) -> dict[str, Any]:
        
        zones = self.coordinator.data.get("zones", [])
        for zone in zones:
            if zone.get("id") == self._zone_id:
                return zone
        return self._zone_data


class AlteregoTemperatureSensor(AlteregoSensorBase):
    

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
        zone_id: str,
        zone_data: dict[str, Any],
    ) -> None:
        
        super().__init__(coordinator, zone_id, zone_data)
        self._attr_name = f"{self._zone_name} Temperature"
        self._sensor_key = "temperature"

    @property
    def native_value(self) -> float | None:
        
        zone = self._get_zone_data()
        status = zone.get("status", {})
        temp = status.get(ATTR_TEMPERATURE)
        if temp in [None, "N/A", "N/C"]:
            return None
        try:
            return float(temp)
        except (ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        
        attrs = super().extra_state_attributes
        zone = self._get_zone_data()
        status = zone.get("status", {})
        attrs[ATTR_TEMPERATURE] = status.get(ATTR_TEMPERATURE)
        attrs["setpoint"] = status.get("current_setpoint")
        return attrs


class AlteregoHumiditySensor(AlteregoSensorBase):
    

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
        zone_id: str,
        zone_data: dict[str, Any],
    ) -> None:
        
        super().__init__(coordinator, zone_id, zone_data)
        self._attr_name = f"{self._zone_name} Humidity"
        self._sensor_key = "humidity"

    @property
    def native_value(self) -> float | None:
        
        zone = self._get_zone_data()
        status = zone.get("status", {})
        humidity = status.get(ATTR_HUMIDITY)
        

        if not humidity or humidity in ["N/C", "N/A", ""]:
            return None
        

        if isinstance(humidity, str):
            humidity = humidity.replace("%", "").strip()
        
        try:
            return float(humidity)
        except (ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        
        attrs = super().extra_state_attributes
        zone = self._get_zone_data()
        params = zone.get("params", {})
        attrs[ATTR_HUMIDITY] = self.native_value
        attrs["setpoint_humidity"] = params.get("setpoint_humidity")
        return attrs


class AlteregoDewpointSensor(AlteregoSensorBase):
    

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
        zone_id: str,
        zone_data: dict[str, Any],
    ) -> None:
        
        super().__init__(coordinator, zone_id, zone_data)
        self._attr_name = f"{self._zone_name} Dewpoint"
        self._sensor_key = "dewpoint"

    @property
    def native_value(self) -> float | None:
        
        zone = self._get_zone_data()
        status = zone.get("status", {})
        dewpoint = status.get(ATTR_DEWPOINT)
        

        if not dewpoint or dewpoint in ["N/C", "N/A", ""]:
            return None
        

        if isinstance(dewpoint, str):
            dewpoint = dewpoint.replace("°C", "").replace("°", "").strip()
        
        try:
            return float(dewpoint)
        except (ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        
        attrs = super().extra_state_attributes
        attrs[ATTR_DEWPOINT] = self.native_value
        return attrs

