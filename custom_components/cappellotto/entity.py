"""Base entities for the Alterego integration."""

from __future__ import annotations

from datetime import time
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    RESOURCE_DEUMS,
    RESOURCE_TIMERS,
    RESOURCE_ZONES,
    TIMER_SLOT_UNUSED,
)
from .coordinator import AlteregoDataUpdateCoordinator

_MISSING_VALUES = (None, "", "N/A", "N/C")

# HA 2026.8 replaced `via_device` (an identifier) with `via_device_id` (a registry id).
_HAS_VIA_DEVICE_ID = "via_device_id" in DeviceInfo.__optional_keys__


def to_float(value: Any) -> float | None:
    """Parse API numbers such as 21.5, "21.5", "55%" or "12.3°C"; None if unusable."""
    if value in _MISSING_VALUES:
        return None
    if isinstance(value, str):
        value = value.replace("°C", "").replace("°", "").replace("%", "").strip()
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_timer_slot(value: str) -> tuple[str, time | None]:
    """Split a slot value like "COMFORT 06:30" into mode and start time."""
    mode, _, start = value.partition(" ")
    try:
        hour, minute = map(int, start.split(":"))
        return mode, time(hour, minute)
    except ValueError:
        return mode, None


class AlteregoEntity(CoordinatorEntity[AlteregoDataUpdateCoordinator]):
    """Base for every Alterego entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AlteregoDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self._station_id = coordinator.station_id


class AlteregoStationEntity(AlteregoEntity):
    """Entity attached to the station device created at setup."""

    def __init__(self, coordinator: AlteregoDataUpdateCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._station_id}_{key}"
        # Identifiers only, so the user's custom station name is not overwritten.
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self._station_id)})


class AlteregoItemEntity(AlteregoEntity):
    """Entity bound to one zone, dehumidifier or timer of the station."""

    _resource: str
    _model: str

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
        item: dict[str, Any],
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._item_id: str = item["id"]
        self._attr_unique_id = f"{self._station_id}_{self._item_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._station_id}_{self._item_id}")},
            name=self._device_name(item),
            manufacturer=MANUFACTURER,
            model=self._model,
        )
        if _HAS_VIA_DEVICE_ID:
            self._attr_device_info["via_device_id"] = coordinator.station_device_id
        else:
            self._attr_device_info["via_device"] = (DOMAIN, self._station_id)

    def _device_name(self, item: dict[str, Any]) -> str:
        description = (item.get("status", {}).get("description") or "").strip()
        return description or f"{self._model} {self._item_id}"

    @property
    def item(self) -> dict[str, Any] | None:
        return self.coordinator.get_item(self._resource, self._item_id)

    @property
    def status(self) -> dict[str, Any]:
        return (self.item or {}).get("status", {})

    @property
    def params(self) -> dict[str, Any]:
        return (self.item or {}).get("params", {})

    @property
    def available(self) -> bool:
        return super().available and self.item is not None

    async def _async_write(self, data: dict[str, Any]) -> None:
        await self.coordinator.async_write(self._resource, data, self._item_id)


class AlteregoZoneEntity(AlteregoItemEntity):
    _resource = RESOURCE_ZONES
    _model = "Zone"


class AlteregoDeumEntity(AlteregoItemEntity):
    _resource = RESOURCE_DEUMS
    _model = "Dehumidifier"

    def _device_name(self, item: dict[str, Any]) -> str:
        # Several units often share the same description, so keep the id.
        description = (item.get("status", {}).get("description") or "").strip()
        return f"{description or 'Deumidificatore'} {self._item_id}"


class AlteregoTimerSlotEntity(AlteregoItemEntity):
    """One weekly slot (e.g. Monday, slot 2) of a timer."""

    _resource = RESOURCE_TIMERS
    _model = "Timer"

    def __init__(
        self,
        coordinator: AlteregoDataUpdateCoordinator,
        timer: dict[str, Any],
        slot_key: str,
        key_suffix: str = "",
    ) -> None:
        super().__init__(coordinator, timer, slot_key + key_suffix)
        self._slot_key = slot_key
        _, day, slot = slot_key.split("_")
        self._attr_translation_key = f"slot{key_suffix}_{day.lower()}"
        self._attr_translation_placeholders = {"slot": str(int(slot) + 1)}

    @property
    def slot_value(self) -> str:
        return self.params.get(self._slot_key, TIMER_SLOT_UNUSED)

    async def _async_write_slot(self, value: str) -> None:
        await self._async_write({self._slot_key: value})
