
import asyncio
from typing import Any, Dict, List, Optional
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


class AlteregoAPIError(Exception):
    pass


class AlteregoAuthenticationError(AlteregoAPIError):
    pass


class AlteregoAPI:
    

    def __init__(
        self,
        username: str,
        password: str,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        
        self._username = username
        self._password = password
        self._session = session
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _ensure_authenticated(self) -> None:
        
        if self._access_token is None:
            await self.authenticate()

    async def authenticate(self) -> Dict[str, Any]:
        
        from .const import OAUTH_URL, CLIENT_ID, CLIENT_SECRET

        session = await self._get_session()

        auth_data = {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "username": self._username,
            "password": self._password,
        }

        try:
            async with session.post(OAUTH_URL, data=auth_data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error("Authentication failed: %s", error_text)
                    raise AlteregoAuthenticationError(f"Authentication failed: {response.status}")

                data = await response.json()
                self._access_token = data.get("access_token")
                expires_in = data.get("expires_in", 31536000)
                self._token_expires_at = asyncio.get_event_loop().time() + expires_in

                _LOGGER.debug("Authentication successful, token expires in %s seconds", expires_in)
                return data
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error during authentication: %s", err)
            raise AlteregoAPIError(f"Network error: {err}") from err

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        
        from .const import API_BASE_URL
        
        await self._ensure_authenticated()

        session = await self._get_session()
        url = f"{API_BASE_URL}/{endpoint}"

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Alterego/1 CFNetwork/3860.300.31 Darwin/25.2.0",
        }

        try:
            async with session.request(
                method,
                url,
                headers=headers,
                json=data,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 401:

                    await self.authenticate()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with session.request(
                        method,
                        url,
                        headers=headers,
                        json=data,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()

                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            _LOGGER.error("API request failed: %s", err)
            raise AlteregoAPIError(f"Request failed: {err}") from err

    async def get_zones(self, station_id: str) -> List[Dict[str, Any]]:
        
        endpoint = f"{station_id}/zones"
        return await self._request("GET", endpoint)

    async def get_global_status(self, station_id: str) -> Dict[str, Any]:
        
        endpoint = f"{station_id}/global"
        return await self._request("GET", endpoint)

    async def get_deums(self, station_id: str) -> List[Dict[str, Any]]:
        
        endpoint = f"{station_id}/deums"
        return await self._request("GET", endpoint)

    async def get_timers(self, station_id: str) -> List[Dict[str, Any]]:
        
        endpoint = f"{station_id}/timers"
        return await self._request("GET", endpoint)

    async def get_stations(self) -> List[Dict[str, Any]]:
        
        from .const import API_BASE_URL
        
        await self._ensure_authenticated()

        session = await self._get_session()

        url = API_BASE_URL

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Alterego/1 CFNetwork/3860.300.31 Darwin/25.2.0",
        }

        try:
            async with session.request(
                "GET",
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 401:

                    await self.authenticate()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with session.request(
                        "GET",
                        url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()

                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            _LOGGER.error("API request failed: %s", err)
            raise AlteregoAPIError(f"Request failed: {err}") from err

    async def update_zone(
        self,
        station_id: str,
        zone_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        
        endpoint = f"{station_id}/zones/{zone_id}"
        return await self._request("POST", endpoint, data=data)

    async def update_timer(
        self,
        station_id: str,
        timer_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        
        endpoint = f"{station_id}/timers/{timer_id}"
        return await self._request("POST", endpoint, data=data)

    async def update_deum(
        self,
        station_id: str,
        deum_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        
        endpoint = f"{station_id}/deums/{deum_id}"
        return await self._request("POST", endpoint, data=data)

    async def update_global(
        self,
        station_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        
        endpoint = f"{station_id}/global"
        return await self._request("POST", endpoint, data=data)

    async def close(self) -> None:
        
        if self._session:
            await self._session.close()

