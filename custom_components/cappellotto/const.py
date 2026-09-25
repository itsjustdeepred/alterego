"""Constants for the Alterego integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "cappellotto"
MANUFACTURER: Final = "Alterego"

CONF_STATION_ID: Final = "station_id"
CONF_STATION_NAME: Final = "station_name"

OAUTH_URL: Final = "https://s5a.eu/oauth/token"
API_BASE_URL: Final = "https://api.s5a.eu/api/v1/stations"
CLIENT_ID: Final = "6"
CLIENT_SECRET: Final = "1H68sl94ep46QtCWNLMelZAiCMcPMRxLpnKmEduS"
USER_AGENT: Final = "Alterego/1 CFNetwork/3860.300.31 Darwin/25.2.0"
REQUEST_TIMEOUT: Final = 10

RESOURCE_ZONES: Final = "zones"
RESOURCE_GLOBAL: Final = "global"
RESOURCE_DEUMS: Final = "deums"
RESOURCE_TIMERS: Final = "timers"

# The coordinator ticks every SCAN_INTERVAL seconds; each resource is fetched
# again only once its own interval has elapsed (or right after a write to it).
SCAN_INTERVAL: Final = 30
UPDATE_INTERVALS: Final[dict[str, int]] = {
    RESOURCE_ZONES: 30,
    RESOURCE_GLOBAL: 300,
    RESOURCE_DEUMS: 60,
    RESOURCE_TIMERS: 300,
}

FORCING_AUTO: Final = "AUTO"
FORCING_OFF: Final = "OFF"
FORCING_ECONOMY: Final = "ECONOMY"
FORCING_COMFORT: Final = "COMFORT"

OVERRIDE_AUTO: Final = "AUTO"
OVERRIDE_LOW: Final = "LOW"
OVERRIDE_MEDIUM: Final = "MEDIUM"
OVERRIDE_HIGH: Final = "HIGH"
OVERRIDE_OFF: Final = "OFF"

SEASON_WINTER: Final = "WINTER"
SEASON_SUMMER: Final = "SUMMER"

TIMER_DAYS: Final = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")
TIMER_SLOTS_PER_DAY: Final = 6
TIMER_SLOT_UNUSED: Final = "N/U"
TIMER_SLOT_MODES: Final = ("COMFORT", "ECONOMY", "OFF")
