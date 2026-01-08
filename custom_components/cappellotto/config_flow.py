from __future__ import annotations

from typing import Any, Dict, List, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

import logging

from .api import AlteregoAPI, AlteregoAuthenticationError, AlteregoAPIError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    pass


class InvalidAuth(HomeAssistantError):
    pass


async def validate_auth(hass: HomeAssistant, data: Dict[str, str]) -> Dict[str, Any]:
    
    api = AlteregoAPI(data["username"], data["password"])

    try:
        await api.authenticate()

        try:
            stations = await api.get_stations()
        except AlteregoAPIError:

            _LOGGER.warning("Failed to get stations list, will use manual input")
            stations = []
        return {"authenticated": True, "stations": stations}
    except AlteregoAuthenticationError as err:
        raise InvalidAuth from err
    except AlteregoAPIError as err:
        raise CannotConnect from err
    finally:
        await api.close()


class AlteregoOptionsFlowHandler(config_entries.OptionsFlow):
    
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        
        if user_input is not None:
            station_name = user_input.get("station_name", "").strip()
            if not station_name:
                station_name = self.config_entry.data.get("station_id")
            
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                title=station_name,
                data={
                    **self.config_entry.data,
                    "station_name": station_name if station_name != self.config_entry.data.get("station_id") else None,
                },
            )
            
            return self.async_create_entry(title="", data={})

        schema = vol.Schema(
            {
                vol.Optional(
                    "station_name",
                    default=self.config_entry.title or self.config_entry.data.get("station_id", "")
                ): cv.string,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={"station_id": self.config_entry.data.get("station_id", "")},
        )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    

    VERSION = 1

    def __init__(self) -> None:
        
        self._username: Optional[str] = None
        self._password: Optional[str] = None
        self._station_id: Optional[str] = None
        self._station_name: Optional[str] = None
        self._stations: List[Dict[str, Any]] = []

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        
        errors: Dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_auth(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                self._username = user_input["username"]
                self._password = user_input["password"]
                self._stations = info.get("stations", [])
                

                if self._stations:
                    return await self.async_step_station_select()
                else:
                    return await self.async_step_station()

        schema = vol.Schema(
            {
                vol.Required("username", default=self._username or ""): cv.string,
                vol.Required("password"): cv.string,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_station(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        
        errors: Dict[str, str] = {}
        
        if user_input is not None:
            self._station_id = user_input["station_id"].strip().upper()


            api = AlteregoAPI(self._username, self._password)
            try:
                await api.authenticate()
                await api.get_zones(self._station_id)
            except AlteregoAPIError as err:
                _LOGGER.error("Station validation failed: %s", err)
                errors["base"] = "invalid_station"
            finally:
                await api.close()

            if not errors:

                await self.async_set_unique_id(self._station_id)
                self._abort_if_unique_id_configured()


                return await self.async_step_station_name()

        schema = vol.Schema(
            {
                vol.Required("station_id", default=self._station_id or ""): cv.string,
            }
        )

        return self.async_show_form(
            step_id="station",
            data_schema=schema,
            errors=errors,
            description_placeholders={"username": self._username or ""},
        )

    async def async_step_station_select(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        
        if user_input is not None:
            self._station_id = user_input["station_id"]
            

            await self.async_set_unique_id(self._station_id)
            self._abort_if_unique_id_configured()


            return await self.async_step_station_name()



        options = {}
        for station in self._stations:
            station_id = station.get("statid", "")
            if station_id:
                options[station_id] = station_id
        
        schema = vol.Schema(
            {
                vol.Required("station_id"): vol.In(options),
            }
        )

        return self.async_show_form(
            step_id="station_select",
            data_schema=schema,
            description_placeholders={"count": str(len(self._stations))},
        )

    async def async_step_station_name(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        
        if user_input is not None:
            self._station_name = user_input.get("station_name", "").strip()
            

            entry_title = self._station_name if self._station_name else self._station_id
            

            if not self._station_id:
                return self.async_abort(reason="no_station_id")
            

            api = AlteregoAPI(self._username, self._password)
            try:
                await api.authenticate()
                await api.get_zones(self._station_id)
            except AlteregoAPIError as err:
                _LOGGER.error("Station validation failed: %s", err)
                await api.close()
                return self.async_show_form(
                    step_id="station_name",
                    data_schema=vol.Schema({
                        vol.Optional("station_name", default=self._station_name or ""): cv.string,
                    }),
                    errors={"base": "invalid_station"},
                    description_placeholders={"station_id": self._station_id or ""},
                )
            finally:
                await api.close()
            
            return self.async_create_entry(
                title=entry_title,
                data={
                    "username": self._username,
                    "password": self._password,
                    "station_id": self._station_id,
                    "station_name": self._station_name or None,
                },
            )

        schema = vol.Schema(
            {
                vol.Optional("station_name", default=""): cv.string,
            }
        )

        return self.async_show_form(
            step_id="station_name",
            data_schema=schema,
            description_placeholders={"station_id": self._station_id or ""},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "AlteregoOptionsFlowHandler":
        
        return AlteregoOptionsFlowHandler(config_entry)


    async def async_step_reconfigure(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        
        errors: Dict[str, str] = {}

        entry_id = self.context.get("entry_id")
        if not entry_id:
            return self.async_abort(reason="no_entry_id")
        
        entry = self.hass.config_entries.async_get_entry(entry_id)
        if not entry:
            return self.async_abort(reason="entry_not_found")
        
        if user_input is not None:

            try:
                await validate_auth(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:

                station_name = user_input.get("station_name", "").strip()
                if not station_name:

                    station_name = entry.data.get("station_name") or entry.data.get("station_id")
                

                self.hass.config_entries.async_update_entry(
                    entry,
                    title=station_name,
                    data={
                        "username": user_input["username"],
                        "password": user_input["password"],
                        "station_id": entry.data["station_id"],
                        "station_name": station_name if station_name != entry.data.get("station_id") else None,
                    },
                )
                

                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        schema = vol.Schema(
            {
                vol.Required("username", default=entry.data.get("username", "")): cv.string,
                vol.Required("password", default=""): cv.string,
                vol.Optional("station_name", default=entry.title or entry.data.get("station_id", "")): cv.string,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
            description_placeholders={"station_id": entry.data.get("station_id", "")},
        )
