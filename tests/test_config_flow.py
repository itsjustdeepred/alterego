"""Tests for the config, reauth, reconfigure and options flows."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.cappellotto.const import API_BASE_URL, DOMAIN

from .conftest import STATION_ID, mock_api

CREDENTIALS = {"username": "user@example.com", "password": "secret"}


async def test_full_flow_with_station_list(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    mock_api(aioclient_mock)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CREDENTIALS
    )
    assert result["step_id"] == "station_select"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station_id": STATION_ID}
    )
    assert result["step_id"] == "station_name"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station_name": "  Home  "}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home"
    assert result["data"] == {
        **CREDENTIALS,
        "station_id": STATION_ID,
        "station_name": "Home",
    }
    assert result["result"].unique_id == STATION_ID


async def test_manual_station_when_list_unavailable(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    mock_api(aioclient_mock, stations=())
    aioclient_mock.get(f"{API_BASE_URL}/DOT_OTHER/zones", status=404)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CREDENTIALS
    )
    assert result["step_id"] == "station"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station_id": "dot_other"}
    )
    # The account cannot read DOT_OTHER.
    assert result["errors"] == {"base": "invalid_station"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station_id": " dot_test "}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == STATION_ID
    assert result["data"]["station_name"] is None


async def test_invalid_auth_and_cannot_connect(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    mock_api(aioclient_mock, auth_status=401)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CREDENTIALS
    )
    assert result["errors"] == {"base": "invalid_auth"}

    mock_api(aioclient_mock, auth_status=503)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CREDENTIALS
    )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_already_configured(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
) -> None:
    config_entry.add_to_hass(hass)
    mock_api(aioclient_mock)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CREDENTIALS
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"station_id": STATION_ID}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
) -> None:
    mock_api(aioclient_mock)
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"username": "user@example.com", "password": "new"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data["password"] == "new"
    assert config_entry.data["station_name"] == "Home"
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(config_entry.entry_id)


async def test_reconfigure(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
) -> None:
    mock_api(aioclient_mock)
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"username": "other@example.com", "password": "pw", "station_name": ""},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.title == STATION_ID
    assert config_entry.data["username"] == "other@example.com"
    assert config_entry.data["station_name"] is None
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(config_entry.entry_id)


async def test_options_rename(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
) -> None:
    mock_api(aioclient_mock)
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"station_name": "Casa"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert config_entry.title == "Casa"
    assert config_entry.data["station_name"] == "Casa"
