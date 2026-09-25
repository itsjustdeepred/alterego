"""Number entities for the Alterego integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SEASON_SUMMER
from .coordinator import AlteregoConfigEntry, AlteregoDataUpdateCoordinator
from .entity import AlteregoDeumEntity, AlteregoZoneEntity, to_float

PARALLEL_UPDATES = 1

SETPOINT_KEYS = (
    "setpoint_comfort_summer",
    "setpoint_economy_summer",
    "setpoint_comfort_winter",
    "setpoint_economy_winter",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlteregoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[NumberEntity] = []

    for zone in coordinator.enabled_zones():
        params = zone.get("params", {})
        entities.extend(
            AlteregoSetpointNumber(coordinator, zone, key)
            for key in SETPOINT_KEYS
            if params.get(key)
        )
        if (
            "RH" in zone.get("status", {}).get("type", "")
            and params.get("setpoint_humidity") is not None
        ):
            entities.append(AlteregoHumiditySetpointNumber(coordinator, zone))

    entities.extend(
        AlteregoDeumBoostTimerNumber(coordinator, deum)
        for deum in coordinator.visible_deums()
    )

    async_add_entities(entities)


class SummerOnlyMixin:
    """Only usable while the station runs in summer mode."""

    coordinator: AlteregoDataUpdateCoordinator

    @property
    def available(self) -> bool:
        return (
            super().available  # type: ignore[misc]
            and self.coordinator.season == SEASON_SUMMER
        )

    def _raise_if_not_summer(self) -> None:
        if self.coordinator.season != SEASON_SUMMER:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="summer_only"
            )


class AlteregoSetpointNumber(AlteregoZoneEntity, NumberEntity):
    """One of the four seasonal comfort/economy setpoints of a zone."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 10.0
    _attr_native_max_value = 30.0
    _attr_native_step = 0.5

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
        zone: dict[str, Any],
        setpoint_key: str,
    ) -> None:
        super().__init__(coordinator, zone, setpoint_key)
        self._setpoint_key = setpoint_key
        self._attr_translation_key = setpoint_key

    @property
    def native_value(self) -> float | None:
        return to_float(self.params.get(self._setpoint_key))

    async def async_set_native_value(self, value: float) -> None:
        await self._async_write({self._setpoint_key: value})


class AlteregoHumiditySetpointNumber(SummerOnlyMixin, AlteregoZoneEntity, NumberEntity):
    """Humidity setpoint of a T+RH zone."""

    _attr_translation_key = "setpoint_humidity"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 30.0
    _attr_native_max_value = 80.0
    _attr_native_step = 0.5

    def __init__(
        self, coordinator: AlteregoDataUpdateCoordinator, zone: dict[str, Any]
    ) -> None:
        super().__init__(coordinator, zone, "setpoint_humidity")

    @property
    def native_value(self) -> float | None:
        return to_float(self.params.get("setpoint_humidity"))

    async def async_set_native_value(self, value: float) -> None:
        self._raise_if_not_summer()
        await self._async_write({"setpoint_humidity": value})


class AlteregoDeumBoostTimerNumber(SummerOnlyMixin, AlteregoDeumEntity, NumberEntity):
    """Duration of the dehumidifier boost."""

    _attr_translation_key = "boost_timer"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_icon = "mdi:timer"

    def __init__(
        self, coordinator: AlteregoDataUpdateCoordinator, deum: dict[str, Any]
    ) -> None:
        super().__init__(coordinator, deum, "boost_timer")

    @property
    def native_value(self) -> float | None:
        return to_float(self.params.get("boost_timer"))

    async def async_set_native_value(self, value: float) -> None:
        self._raise_if_not_summer()
        params = self.params
        # The API expects the fan speeds to be sent together with the timer.
        await self._async_write(
            {
                "boost_timer": int(value),
                "vent_speed_boost": params.get("vent_speed_boost", 80),
                "vent_speed_comfort": params.get("vent_speed_comfort", 40),
                "vent_speed_economy": params.get("vent_speed_economy", 0),
            }
        )
