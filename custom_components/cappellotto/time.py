"""Time entities (timer slot start times) for the Alterego integration."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import TIMER_SLOT_MODES, TIMER_SLOT_UNUSED
from .coordinator import AlteregoConfigEntry
from .entity import AlteregoTimerSlotEntity, parse_timer_slot

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlteregoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        AlteregoTimerSlotTime(coordinator, timer, slot_key, "_time")
        for timer, slot_key in coordinator.active_timer_slots()
    )


class AlteregoTimerSlotTime(AlteregoTimerSlotEntity, TimeEntity):
    """Start time of a timer slot; unavailable while the slot is unused."""

    _attr_icon = "mdi:clock-time-four"

    @property
    def _start(self) -> time | None:
        if self.slot_value == TIMER_SLOT_UNUSED:
            return None
        return parse_timer_slot(self.slot_value)[1]

    @property
    def available(self) -> bool:
        return super().available and self._start is not None

    @property
    def native_value(self) -> time | None:
        return self._start

    async def async_set_value(self, value: time) -> None:
        mode = TIMER_SLOT_MODES[0]
        if self.slot_value != TIMER_SLOT_UNUSED:
            mode = parse_timer_slot(self.slot_value)[0] or mode
        await self._async_write_slot(f"{mode} {value.strftime('%H:%M')}")
