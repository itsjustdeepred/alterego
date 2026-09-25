"""Sensor entities for the Alterego integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import RESOURCE_GLOBAL
from .coordinator import AlteregoConfigEntry, AlteregoDataUpdateCoordinator
from .entity import AlteregoStationEntity, AlteregoZoneEntity, to_float


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlteregoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []

    if coordinator.data[RESOURCE_GLOBAL]:
        entities.append(AlteregoGlobalSensor(coordinator))
        entities.append(AlteregoOutsideTemperatureSensor(coordinator))

    for zone in coordinator.enabled_zones():
        status = zone.get("status", {})
        if to_float(status.get("temperature")) is not None:
            entities.append(AlteregoTemperatureSensor(coordinator, zone))
        if "RH" in status.get("type", ""):
            if to_float(status.get("humidity")) is not None:
                entities.append(AlteregoHumiditySensor(coordinator, zone))
            if to_float(status.get("dewpoint")) is not None:
                entities.append(AlteregoDewpointSensor(coordinator, zone))

    async_add_entities(entities)


class AlteregoGlobalSensor(AlteregoStationEntity, SensorEntity):
    """Overall station status."""

    _attr_translation_key = "status"
    _attr_icon = "mdi:home-thermometer"

    def __init__(self, coordinator: AlteregoDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "global_status")

    @property
    def _global(self) -> dict[str, Any]:
        return self.coordinator.data[RESOURCE_GLOBAL]

    @property
    def native_value(self) -> str | None:
        return self._global.get("status", {}).get("global_status")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        status = self._global.get("status", {})
        return {
            "season": status.get("global_season"),
            "outside_temperature": to_float(status.get("outside_temp")),
            "last_connection": status.get("last_connection"),
            "global_enable": self._global.get("params", {}).get("global_enable"),
        }


class AlteregoOutsideTemperatureSensor(AlteregoStationEntity, SensorEntity):
    """Outside temperature measured by the station."""

    _attr_translation_key = "outside_temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: AlteregoDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "outside_temperature")

    @property
    def native_value(self) -> float | None:
        status = self.coordinator.data[RESOURCE_GLOBAL].get("status", {})
        return to_float(status.get("outside_temp"))


class AlteregoZoneSensor(AlteregoZoneEntity, SensorEntity):
    """A measurement read from the zone status."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _status_key: str

    def __init__(
        self, coordinator: AlteregoDataUpdateCoordinator, zone: dict[str, Any]
    ) -> None:
        super().__init__(coordinator, zone, self._status_key)
        self._attr_translation_key = self._status_key

    @property
    def native_value(self) -> float | None:
        return to_float(self.status.get(self._status_key))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        status = self.status
        return {
            "zone_id": self._item_id,
            "zone_name": self.device_info["name"],
            "zone_type": status.get("type"),
            "enabled": status.get("enabled"),
            "current_mode": status.get("current_mode"),
            "zone_output": status.get("zone_output"),
            self._status_key: self.native_value,
        }


class AlteregoTemperatureSensor(AlteregoZoneSensor):
    _status_key = "temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            **super().extra_state_attributes,
            "setpoint": self.status.get("current_setpoint"),
        }


class AlteregoHumiditySensor(AlteregoZoneSensor):
    _status_key = "humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            **super().extra_state_attributes,
            "setpoint_humidity": self.params.get("setpoint_humidity"),
        }


class AlteregoDewpointSensor(AlteregoZoneSensor):
    _status_key = "dewpoint"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
