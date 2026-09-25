"""Config flow for the Alterego integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import AlteregoAPI, AlteregoAPIError, AlteregoAuthenticationError
from .const import CONF_STATION_ID, CONF_STATION_NAME, DOMAIN, RESOURCE_ZONES

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


def _station_name(user_input: Mapping[str, Any], station_id: str) -> str | None:
    """Custom name, or None when empty or equal to the station id."""
    name = (user_input.get(CONF_STATION_NAME) or "").strip()
    return name if name and name != station_id else None


class AlteregoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up an Alterego station."""

    VERSION = 1

    def __init__(self) -> None:
        self._username = ""
        self._password = ""
        self._station_id = ""
        self._stations: list[str] = []

    async def _async_check(
        self, username: str, password: str, station_id: str | None = None
    ) -> tuple[AlteregoAPI | None, dict[str, str]]:
        """Log in and optionally check the station is readable; return errors."""
        api = AlteregoAPI(async_get_clientsession(self.hass), username, password)
        try:
            await api.authenticate()
        except AlteregoAuthenticationError:
            return None, {"base": "invalid_auth"}
        except AlteregoAPIError:
            return None, {"base": "cannot_connect"}
        except Exception:
            _LOGGER.exception("Unexpected error while authenticating")
            return None, {"base": "unknown"}

        if station_id is not None:
            try:
                await api.get_resource(station_id, RESOURCE_ZONES)
            except AlteregoAPIError as err:
                _LOGGER.debug("Station %s not accessible: %s", station_id, err)
                return None, {"base": "invalid_station"}
        return api, {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the account credentials."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api, errors = await self._async_check(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if api is not None:
                self._username = user_input[CONF_USERNAME]
                self._password = user_input[CONF_PASSWORD]
                try:
                    stations = await api.get_stations()
                except AlteregoAPIError as err:
                    _LOGGER.warning(
                        "Could not list stations, asking for the id: %s", err
                    )
                    stations = []
                self._stations = [s["statid"] for s in stations if s.get("statid")]
                if self._stations:
                    return await self.async_step_station_select()
                return await self.async_step_station()

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_SCHEMA, {CONF_USERNAME: self._username}
            ),
            errors=errors,
        )

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the station id when the account cannot list its stations."""
        errors: dict[str, str] = {}
        if user_input is not None:
            station_id = user_input[CONF_STATION_ID].strip().upper()
            _, errors = await self._async_check(
                self._username, self._password, station_id
            )
            if not errors:
                return await self._async_select_station(station_id)

        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema(
                {vol.Required(CONF_STATION_ID, default=self._station_id): str}
            ),
            errors=errors,
        )

    async def async_step_station_select(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick one of the stations of the account."""
        if user_input is not None:
            return await self._async_select_station(user_input[CONF_STATION_ID])

        return self.async_show_form(
            step_id="station_select",
            data_schema=vol.Schema(
                {vol.Required(CONF_STATION_ID): vol.In(self._stations)}
            ),
            description_placeholders={"count": str(len(self._stations))},
        )

    async def _async_select_station(self, station_id: str) -> ConfigFlowResult:
        self._station_id = station_id
        await self.async_set_unique_id(station_id)
        self._abort_if_unique_id_configured()
        return await self.async_step_station_name()

    async def async_step_station_name(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Optionally give the station a friendlier name."""
        if user_input is not None:
            name = _station_name(user_input, self._station_id)
            return self.async_create_entry(
                title=name or self._station_id,
                data={
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_STATION_ID: self._station_id,
                    CONF_STATION_NAME: name,
                },
            )

        return self.async_show_form(
            step_id="station_name",
            data_schema=vol.Schema({vol.Optional(CONF_STATION_NAME, default=""): str}),
            description_placeholders={"station_id": self._station_id},
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start re-authentication after the API rejected the credentials."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for new credentials."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            _, errors = await self._async_check(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                entry.data[CONF_STATION_ID],
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_SCHEMA, {CONF_USERNAME: entry.data[CONF_USERNAME]}
            ),
            errors=errors,
            description_placeholders={"station_id": entry.data[CONF_STATION_ID]},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change credentials and name of an existing station."""
        entry = self._get_reconfigure_entry()
        station_id = entry.data[CONF_STATION_ID]
        errors: dict[str, str] = {}
        if user_input is not None:
            _, errors = await self._async_check(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD], station_id
            )
            if not errors:
                name = _station_name(user_input, station_id)
                return self.async_update_reload_and_abort(
                    entry,
                    title=name or station_id,
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_STATION_NAME: name,
                    },
                )

        schema = STEP_USER_SCHEMA.extend({vol.Optional(CONF_STATION_NAME): str})
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                schema,
                {
                    CONF_USERNAME: entry.data[CONF_USERNAME],
                    CONF_STATION_NAME: entry.data.get(CONF_STATION_NAME) or "",
                },
            ),
            errors=errors,
            description_placeholders={"station_id": station_id},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> AlteregoOptionsFlow:
        return AlteregoOptionsFlow()


class AlteregoOptionsFlow(OptionsFlow):
    """Rename the station."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self.config_entry
        station_id = entry.data[CONF_STATION_ID]
        if user_input is not None:
            name = _station_name(user_input, station_id)
            self.hass.config_entries.async_update_entry(
                entry,
                title=name or station_id,
                data={**entry.data, CONF_STATION_NAME: name},
            )
            # Reload so the station device picks up the new name.
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_STATION_NAME,
                        description={
                            "suggested_value": entry.data.get(CONF_STATION_NAME) or ""
                        },
                    ): str
                }
            ),
            description_placeholders={"station_id": station_id},
        )
