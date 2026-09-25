"""Climate entities (one per zone) for the Alterego integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    FORCING_AUTO,
    FORCING_COMFORT,
    FORCING_ECONOMY,
    FORCING_OFF,
    SEASON_SUMMER,
)
from .coordinator import AlteregoConfigEntry, AlteregoDataUpdateCoordinator
from .entity import AlteregoZoneEntity, to_float

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlteregoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        AlteregoClimate(coordinator, zone) for zone in coordinator.enabled_zones()
    )


class AlteregoClimate(AlteregoZoneEntity, ClimateEntity):
    """A zone: target temperature, forcing presets and heat/cool/off."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_preset_modes = [FORCING_AUTO, FORCING_COMFORT, FORCING_ECONOMY, FORCING_OFF]

    def __init__(
        self, coordinator: AlteregoDataUpdateCoordinator, zone: dict[str, Any]
    ) -> None:
        super().__init__(coordinator, zone, "climate")

    @property
    def _is_summer(self) -> bool:
        return self.coordinator.season == SEASON_SUMMER

    @property
    def current_temperature(self) -> float | None:
        return to_float(self.status.get("temperature"))

    @property
    def target_temperature(self) -> float | None:
        # The API reports 0.0 when the zone has no active setpoint.
        return to_float(self.status.get("current_setpoint")) or None

    @property
    def hvac_modes(self) -> list[HVACMode]:
        if self._is_summer:
            return [HVACMode.COOL, HVACMode.OFF]
        return [HVACMode.HEAT, HVACMode.OFF]

    @property
    def hvac_mode(self) -> HVACMode:
        if self.preset_mode == FORCING_OFF:
            return HVACMode.OFF
        return HVACMode.COOL if self._is_summer else HVACMode.HEAT

    @property
    def preset_mode(self) -> str:
        return self.params.get("forcing", FORCING_AUTO)

    def _season_limit(self, bound: str, default: float) -> float:
        season = "summer" if self._is_summer else "winter"
        value = to_float(
            self.coordinator.global_params.get(f"global_zset_{bound}_{season}")
        )
        return default if value is None else value

    @property
    def min_temp(self) -> float:
        return self._season_limit("min", 15.0 if self._is_summer else 10.0)

    @property
    def max_temp(self) -> float:
        return self._season_limit("max", 30.0)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        # In AUTO/OFF the comfort setpoint is the one that matters.
        level = "economy" if self.preset_mode == FORCING_ECONOMY else "comfort"
        season = "summer" if self._is_summer else "winter"
        await self._async_write({f"setpoint_{level}_{season}": temperature})

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self.async_set_preset_mode(FORCING_OFF)
        elif self.preset_mode == FORCING_OFF:
            # Only leave OFF; an active COMFORT/ECONOMY forcing is kept.
            await self.async_set_preset_mode(FORCING_AUTO)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self._async_write({"forcing": preset_mode})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        params = self.params
        return {
            "zone_id": self._item_id,
            "zone_type": self.status.get("type"),
            "current_mode": self.status.get("current_mode"),
            "zone_output": self.status.get("zone_output"),
            "setpoint_comfort_summer": params.get("setpoint_comfort_summer"),
            "setpoint_comfort_winter": params.get("setpoint_comfort_winter"),
            "setpoint_economy_summer": params.get("setpoint_economy_summer"),
            "setpoint_economy_winter": params.get("setpoint_economy_winter"),
        }
