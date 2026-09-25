"""Client for the Alterego cloud API."""

from __future__ import annotations

import logging
import time
from typing import Any

import aiohttp

from .const import (
    API_BASE_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    OAUTH_URL,
    REQUEST_TIMEOUT,
    USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
# Refresh the token this many seconds before it actually expires.
_TOKEN_EXPIRY_MARGIN = 60


class AlteregoAPIError(Exception):
    """Generic error talking to the Alterego API."""


class AlteregoAuthenticationError(AlteregoAPIError):
    """Credentials or access token rejected."""


class AlteregoAPI:
    """Thin async wrapper around the Alterego REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    async def authenticate(self) -> None:
        """Obtain a new access token with the password grant."""
        auth_data = {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "username": self._username,
            "password": self._password,
        }
        try:
            async with self._session.post(
                OAUTH_URL, data=auth_data, timeout=_TIMEOUT
            ) as response:
                if response.status in (400, 401, 403):
                    _LOGGER.debug(
                        "Authentication rejected (%s): %s",
                        response.status,
                        await response.text(),
                    )
                    raise AlteregoAuthenticationError(
                        f"Authentication rejected: HTTP {response.status}"
                    )
                response.raise_for_status()
                data = await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise AlteregoAPIError(f"Authentication request failed: {err!r}") from err

        token = data.get("access_token")
        if not token:
            raise AlteregoAuthenticationError("No access token in OAuth response")
        expires_in = data.get("expires_in", 31536000)
        self._access_token = token
        self._token_expires_at = time.monotonic() + expires_in
        _LOGGER.debug("Authenticated, token expires in %s seconds", expires_in)

    async def _ensure_authenticated(self) -> None:
        if (
            self._access_token is None
            or time.monotonic() >= self._token_expires_at - _TOKEN_EXPIRY_MARGIN
        ):
            await self.authenticate()

    async def _request(
        self, method: str, endpoint: str = "", data: dict[str, Any] | None = None
    ) -> Any:
        """Send a request, re-authenticating once if the token is rejected."""
        await self._ensure_authenticated()
        try:
            return await self._send(method, endpoint, data)
        except AlteregoAuthenticationError:
            _LOGGER.debug("Access token rejected, re-authenticating")
            await self.authenticate()
            return await self._send(method, endpoint, data)

    async def _send(
        self, method: str, endpoint: str, data: dict[str, Any] | None
    ) -> Any:
        url = f"{API_BASE_URL}/{endpoint}" if endpoint else API_BASE_URL
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        try:
            async with self._session.request(
                method, url, headers=headers, json=data, timeout=_TIMEOUT
            ) as response:
                if response.status == 401:
                    raise AlteregoAuthenticationError("Access token rejected")
                response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise AlteregoAPIError(f"{method} {url} failed: {err!r}") from err

    @staticmethod
    def _numeric_id(resource_id: str) -> str:
        """Write endpoints want "1" where read endpoints return "Z1"/"T1"/"D1"."""
        return resource_id.lstrip(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        )

    async def get_stations(self) -> list[dict[str, Any]]:
        """Return the stations visible to the account."""
        return await self._request("GET")

    async def get_resource(self, station_id: str, resource: str) -> Any:
        """Read zones, global, deums or timers of a station."""
        return await self._request("GET", f"{station_id}/{resource}")

    async def update_global(self, station_id: str, data: dict[str, Any]) -> Any:
        """Write station-wide parameters."""
        return await self._request("POST", f"{station_id}/global", data)

    async def update_item(
        self, station_id: str, resource: str, item_id: str, data: dict[str, Any]
    ) -> Any:
        """Write parameters of a single zone, deum or timer."""
        endpoint = f"{station_id}/{resource}/{self._numeric_id(item_id)}"
        return await self._request("POST", endpoint, data)
