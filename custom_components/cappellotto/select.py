"""Select entities for the Alterego integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    FORCING_AUTO,
    FORCING_COMFORT,
    FORCING_ECONOMY,
    FORCING_OFF,
    OVERRIDE_AUTO,
    OVERRIDE_HIGH,
    OVERRIDE_LOW,
    OVERRIDE_MEDIUM,
    OVERRIDE_OFF,
    RESOURCE_GLOBAL,
    SEASON_SUMMER,
    SEASON_WINTER,
    TIMER_SLOT_MODES,
    TIMER_SLOT_UNUSED,
)
from .coordinator import AlteregoConfigEntry, AlteregoDataUpdateCoordinator
from .entity import (
    AlteregoDeumEntity,
    AlteregoStationEntity,
    AlteregoTimerSlotEntity,
    AlteregoZoneEntity,
    parse_timer_slot,
)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlteregoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SelectEntity] = [
        AlteregoZoneForcingSelect(coordinator, zone)
        for zone in coordinator.enabled_zones()
    ]
    entities.extend(
        AlteregoDeumOverrideSelect(coordinator, deum)
        for deum in coordinator.visible_deums()
    )
    entities.extend(
        AlteregoTimerSlotSelect(coordinator, timer, slot_key)
        for timer, slot_key in coordinator.active_timer_slots()
    )
    if coordinator.data[RESOURCE_GLOBAL]:
        entities.append(AlteregoSeasonSelect(coordinator))

    async_add_entities(entities)


class AlteregoZoneForcingSelect(AlteregoZoneEntity, SelectEntity):
    """Zone forcing mode."""

    _attr_translation_key = "forcing_mode"
    _attr_options = [FORCING_AUTO, FORCING_COMFORT, FORCING_ECONOMY, FORCING_OFF]
    _attr_icon = "mdi:thermostat"

    def __init__(
        self, coordinator: AlteregoDataUpdateCoordinator, zone: dict[str, Any]
    ) -> None:
        super().__init__(coordinator, zone, "forcing")

    @property
    def current_option(self) -> str:
        return self.params.get("forcing", FORCING_AUTO)

    async def async_select_option(self, option: str) -> None:
        await self._async_write({"forcing": option})


class AlteregoDeumOverrideSelect(AlteregoDeumEntity, SelectEntity):
    """Dehumidifier / VMC speed override."""

    _attr_translation_key = "deum_override"
    _attr_options = [
        OVERRIDE_AUTO,
        OVERRIDE_LOW,
        OVERRIDE_MEDIUM,
        OVERRIDE_HIGH,
        OVERRIDE_OFF,
    ]
    _attr_icon = "mdi:air-humidifier"

    def __init__(
        self, coordinator: AlteregoDataUpdateCoordinator, deum: dict[str, Any]
    ) -> None:
        super().__init__(coordinator, deum, "override")

    @property
    def current_option(self) -> str:
        return self.params.get("user_override", OVERRIDE_AUTO)

    async def async_select_option(self, option: str) -> None:
        await self._async_write({"user_override": option})


class AlteregoSeasonSelect(AlteregoStationEntity, SelectEntity):
    """Station-wide season."""

    _attr_translation_key = "season"
    _attr_options = [SEASON_WINTER, SEASON_SUMMER]
    _attr_icon = "mdi:weather-snowy-rainy"

    def __init__(self, coordinator: AlteregoDataUpdateCoordinator) -> None:
        super().__init__(coordinator, "season")

    @property
    def current_option(self) -> str:
        return self.coordinator.global_params.get("global_set_season", SEASON_WINTER)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_write(
            RESOURCE_GLOBAL, {"global_set_season": option}
        )


class AlteregoTimerSlotSelect(AlteregoTimerSlotEntity, SelectEntity):
    """Mode of a timer slot; N/U disables the slot."""

    _attr_icon = "mdi:timer"
    _attr_options = [*TIMER_SLOT_MODES, TIMER_SLOT_UNUSED]

    @property
    def current_option(self) -> str:
        value = self.slot_value
        if value == TIMER_SLOT_UNUSED:
            return value
        return parse_timer_slot(value)[0]

    async def async_select_option(self, option: str) -> None:
        if option == TIMER_SLOT_UNUSED:
            await self._async_write_slot(TIMER_SLOT_UNUSED)
            return
        start = None
        if self.slot_value != TIMER_SLOT_UNUSED:
            start = parse_timer_slot(self.slot_value)[1]
        start_str = start.strftime("%H:%M") if start else "00:00"
        await self._async_write_slot(f"{option} {start_str}")
