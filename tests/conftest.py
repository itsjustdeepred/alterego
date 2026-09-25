"""Fixtures for the Alterego tests."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.cappellotto.const import API_BASE_URL, DOMAIN, OAUTH_URL

STATION_ID = "DOT_TEST"
STATION_URL = f"{API_BASE_URL}/{STATION_ID}"

ZONES: list[dict[str, Any]] = [
    {
        "id": "Z1",
        "status": {
            "enabled": 1,
            "description": "Living",
            "type": "T+RH",
            "temperature": "21.5",
            "humidity": "55%",
            "dewpoint": "12.1°C",
            "current_setpoint": "21.0",
        },
        "params": {
            "forcing": "AUTO",
            "setpoint_comfort_summer": "25.0",
            "setpoint_economy_summer": "27.0",
            "setpoint_comfort_winter": "21.0",
            "setpoint_economy_winter": "18.0",
            "setpoint_humidity": "55.0",
        },
    },
    {"id": "Z2", "status": {"enabled": 0, "description": "Unused"}, "params": {}},
]
GLOBAL: dict[str, Any] = {
    "data": {
        "status": {
            "global_season": "WINTER",
            "global_status": "ON",
            "outside_temp": "8.5",
        },
        "params": {
            "global_set_season": "WINTER",
            "global_zset_min_winter": "12.0",
            "global_zset_max_winter": "26.0",
        },
    }
}
DEUMS: list[dict[str, Any]] = [
    {
        "id": "D1",
        "status": {"enabled": 1, "user_visible": True, "description": "Deum"},
        "params": {"user_override": "AUTO", "boost_timer": 10},
    },
    # The API sometimes lists the same unit twice.
    {
        "id": "D1",
        "status": {"enabled": 1, "user_visible": True, "description": "Deum"},
        "params": {"user_override": "AUTO", "boost_timer": 10},
    },
    {"id": "D2", "status": {"enabled": 1, "user_visible": False}, "params": {}},
]
TIMERS: list[dict[str, Any]] = [
    {
        "id": "T1",
        "status": {"enabled": 1, "description": "Timer"},
        "params": {
            "S_MO_0": "COMFORT 06:30",
            "S_MO_1": "N/U",
            "S_TU_2": "ECONOMY 22:00",
        },
    }
]


def mock_api(
    aioclient_mock: AiohttpClientMocker,
    *,
    zones: Any = ZONES,
    global_: Any = GLOBAL,
    deums: Any = DEUMS,
    timers: Any = TIMERS,
    stations: Any = ({"statid": STATION_ID},),
    auth_status: int = 200,
) -> None:
    """Register responses for every endpoint; pass an Exception to fail one."""
    aioclient_mock.clear_requests()
    aioclient_mock.post(
        OAUTH_URL,
        status=auth_status,
        json={"access_token": "token", "expires_in": 3600},
    )

    def register(url: str, payload: Any) -> None:
        if isinstance(payload, Exception):
            aioclient_mock.get(url, exc=payload)
        else:
            aioclient_mock.get(url, json=copy.deepcopy(payload))

    register(API_BASE_URL, list(stations))
    register(f"{STATION_URL}/zones", zones)
    register(f"{STATION_URL}/global", global_)
    register(f"{STATION_URL}/deums", deums)
    register(f"{STATION_URL}/timers", timers)
    for resource in ("zones/1", "deums/1", "timers/1", "global"):
        aioclient_mock.post(f"{STATION_URL}/{resource}", json={"result": "ok"})


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow loading custom_components in every test."""
    return


@pytest.fixture
def config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=STATION_ID,
        title="Home",
        data={
            "username": "user@example.com",
            "password": "secret",
            "station_id": STATION_ID,
            "station_name": "Home",
        },
    )
