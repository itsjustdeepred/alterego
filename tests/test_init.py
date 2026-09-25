"""Tests for setup, the coordinator and the entities."""

from __future__ import annotations

from datetime import timedelta
import json

from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.cappellotto.const import DOMAIN

from .conftest import GLOBAL, STATION_ID, STATION_URL, TIMERS, mock_api


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_creates_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    mock_api(aioclient_mock)
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED

    registry = er.async_get(hass)
    unique_ids = {
        e.unique_id
        for e in er.async_entries_for_config_entry(registry, config_entry.entry_id)
    }
    # Unique ids must stay identical to v1.1.x so existing entities are kept.
    assert unique_ids == {
        f"{STATION_ID}_global_status",
        f"{STATION_ID}_outside_temperature",
        f"{STATION_ID}_season",
        f"{STATION_ID}_Z1_climate",
        f"{STATION_ID}_Z1_temperature",
        f"{STATION_ID}_Z1_humidity",
        f"{STATION_ID}_Z1_dewpoint",
        f"{STATION_ID}_Z1_forcing",
        f"{STATION_ID}_Z1_setpoint_comfort_summer",
        f"{STATION_ID}_Z1_setpoint_economy_summer",
        f"{STATION_ID}_Z1_setpoint_comfort_winter",
        f"{STATION_ID}_Z1_setpoint_economy_winter",
        f"{STATION_ID}_Z1_setpoint_humidity",
        f"{STATION_ID}_D1_override",
        f"{STATION_ID}_D1_boost_timer",
        f"{STATION_ID}_T1_S_MO_0",
        f"{STATION_ID}_T1_S_TU_2",
        f"{STATION_ID}_T1_S_MO_0_time",
        f"{STATION_ID}_T1_S_TU_2_time",
    }

    climate = hass.states.get("climate.living")
    assert climate.state == "heat"
    assert climate.attributes["current_temperature"] == 21.5
    assert climate.attributes["temperature"] == 21.0
    assert climate.attributes["min_temp"] == 12.0
    assert climate.attributes["max_temp"] == 26.0
    assert hass.states.get("sensor.living_humidity").state == "55.0"
    assert hass.states.get("sensor.living_dewpoint").state == "12.1"
    assert hass.states.get("sensor.home_outside_temperature").state == "8.5"
    assert hass.states.get("select.timer_monday_slot_1").state == "COMFORT"
    assert hass.states.get("time.timer_monday_slot_1_time").state == "06:30:00"
    # Humidity setpoint and boost timer are summer-only.
    assert hass.states.get("number.living_humidity_setpoint").state == STATE_UNAVAILABLE


async def test_custom_station_name_is_kept(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    mock_api(aioclient_mock)
    await _setup(hass, config_entry)
    registry = dr.async_get(hass)
    station = registry.async_get_device_by_identifier(
        (DOMAIN, STATION_ID), config_entry.entry_id
    )
    assert station.name == "Home"
    zone = registry.async_get_device_by_identifier(
        (DOMAIN, f"{STATION_ID}_Z1"), config_entry.entry_id
    )
    assert zone.name == "Living"
    assert zone.via_device_id == station.id


async def test_setup_retries_when_api_down(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    mock_api(aioclient_mock, zones=TimeoutError())
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_bad_credentials_start_reauth(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    mock_api(aioclient_mock, auth_status=401)
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert [f["context"]["source"] for f in flows] == [SOURCE_REAUTH]


async def test_entities_unavailable_when_zones_fail(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
) -> None:
    mock_api(aioclient_mock)
    await _setup(hass, config_entry)
    assert hass.states.get("climate.living").state == "heat"

    mock_api(aioclient_mock, zones=TimeoutError())
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("climate.living").state == STATE_UNAVAILABLE
    assert hass.states.get("sensor.living_temperature").state == STATE_UNAVAILABLE


async def test_optional_resource_failure_keeps_last_data(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
) -> None:
    mock_api(aioclient_mock)
    await _setup(hass, config_entry)

    mock_api(aioclient_mock, deums=TimeoutError(), timers=TimeoutError())
    freezer.tick(timedelta(seconds=301))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("climate.living").state == "heat"
    assert hass.states.get("select.deum_d1_override").state == "AUTO"
    assert hass.states.get("select.timer_monday_slot_1").state == "COMFORT"


async def test_season_change_is_visible_immediately(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Global data is cached for 5 minutes, but a write must bypass the cache."""
    mock_api(aioclient_mock)
    await _setup(hass, config_entry)

    summer = json.loads(json.dumps(GLOBAL))
    summer["data"]["status"]["global_season"] = "SUMMER"
    summer["data"]["params"]["global_set_season"] = "SUMMER"
    mock_api(aioclient_mock, global_=summer)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.home_season", "option": "SUMMER"},
        blocking=True,
    )
    await hass.async_block_till_done()

    write = [
        c for c in aioclient_mock.mock_calls if c[0] == "POST" and "global" in str(c[1])
    ]
    assert write[0][2] == {"global_set_season": "SUMMER"}
    assert hass.states.get("select.home_season").state == "SUMMER"
    assert hass.states.get("climate.living").state == "cool"
    assert hass.states.get("number.living_humidity_setpoint").state == "55.0"


async def test_timer_slot_write(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    mock_api(aioclient_mock)
    await _setup(hass, config_entry)

    updated = json.loads(json.dumps(TIMERS))
    updated[0]["params"]["S_MO_0"] = "COMFORT 07:15"
    mock_api(aioclient_mock, timers=updated)
    await hass.services.async_call(
        "time",
        "set_value",
        {"entity_id": "time.timer_monday_slot_1_time", "time": "07:15"},
        blocking=True,
    )
    await hass.async_block_till_done()

    posts = [
        c for c in aioclient_mock.mock_calls if c[0] == "POST" and "timers" in str(c[1])
    ]
    assert posts[0][2] == {"S_MO_0": "COMFORT 07:15"}
    assert hass.states.get("time.timer_monday_slot_1_time").state == "07:15:00"

    # Disabling a slot must send a bare "N/U", not "N/U 07:15".
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.timer_monday_slot_1", "option": "N/U"},
        blocking=True,
    )
    posts = [
        c for c in aioclient_mock.mock_calls if c[0] == "POST" and "timers" in str(c[1])
    ]
    assert posts[-1][2] == {"S_MO_0": "N/U"}


async def test_climate_actions(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    mock_api(aioclient_mock)
    await _setup(hass, config_entry)

    def zone_posts() -> list:
        return [
            c[2]
            for c in aioclient_mock.mock_calls
            if c[0] == "POST" and "zones/1" in str(c[1])
        ]

    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": "climate.living", "temperature": 22.5},
        blocking=True,
    )
    await hass.services.async_call(
        "climate", "turn_off", {"entity_id": "climate.living"}, blocking=True
    )
    # Already on (AUTO): selecting heat must not touch the forcing.
    await hass.services.async_call(
        "climate",
        "set_hvac_mode",
        {"entity_id": "climate.living", "hvac_mode": "heat"},
        blocking=True,
    )
    assert zone_posts() == [{"setpoint_comfort_winter": 22.5}, {"forcing": "OFF"}]


async def test_write_error_is_reported(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    mock_api(aioclient_mock)
    await _setup(hass, config_entry)
    aioclient_mock.clear_requests()
    mock_api(aioclient_mock)
    # Re-register the zone write so that it fails.
    aioclient_mock._mocks = [
        m for m in aioclient_mock._mocks if not str(m.url).endswith("zones/1")
    ]
    aioclient_mock.post(f"{STATION_URL}/zones/1", status=500)

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": "select.living_mode", "option": "COMFORT"},
            blocking=True,
        )


async def test_unload(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    mock_api(aioclient_mock)
    await _setup(hass, config_entry)
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED
