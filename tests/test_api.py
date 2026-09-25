"""Tests for the API client."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.cappellotto.api import (
    AlteregoAPI,
    AlteregoAPIError,
    AlteregoAuthenticationError,
)
from custom_components.cappellotto.const import OAUTH_URL

from .conftest import STATION_ID, STATION_URL, mock_api


def _api(hass: HomeAssistant) -> AlteregoAPI:
    return AlteregoAPI(async_get_clientsession(hass), "user", "pw")


async def test_timeout_is_wrapped(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    mock_api(aioclient_mock, zones=TimeoutError())
    with pytest.raises(AlteregoAPIError):
        await _api(hass).get_resource(STATION_ID, "zones")


async def test_rejected_token_triggers_one_relogin(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    mock_api(aioclient_mock)
    aioclient_mock._mocks = [
        m for m in aioclient_mock._mocks if not str(m.url).endswith("/zones")
    ]
    aioclient_mock.get(f"{STATION_URL}/zones", status=401)

    with pytest.raises(AlteregoAuthenticationError):
        await _api(hass).get_resource(STATION_ID, "zones")
    logins = [c for c in aioclient_mock.mock_calls if str(c[1]) == OAUTH_URL]
    assert len(logins) == 2


async def test_write_strips_id_prefix(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    mock_api(aioclient_mock)
    await _api(hass).update_item(STATION_ID, "zones", "Z1", {"forcing": "OFF"})
    assert aioclient_mock.mock_calls[-1][1].path.endswith("/zones/1")
