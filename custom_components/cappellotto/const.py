
from typing import Final

DOMAIN: Final = "cappellotto"


OAUTH_URL: Final = "https://s5a.eu/oauth/token"
API_BASE_URL: Final = "https://api.s5a.eu/api/v1/stations"


CLIENT_ID: Final = "6"
CLIENT_SECRET: Final = "1H68sl94ep46QtCWNLMelZAiCMcPMRxLpnKmEduS"


UPDATE_INTERVAL_ZONES: Final = 60
UPDATE_INTERVAL_GLOBAL: Final = 300
UPDATE_INTERVAL_DEUMS: Final = 60
UPDATE_INTERVAL_TIMERS: Final = 300


RATE_LIMIT_REQUESTS: Final = 6000
RATE_LIMIT_WINDOW: Final = 3600
SAFE_REFRESH_INTERVAL: Final = 30


DEVICE_TYPE_ZONE: Final = "zone"
DEVICE_TYPE_DEUM: Final = "deum"
DEVICE_TYPE_TIMER: Final = "timer"
DEVICE_TYPE_GLOBAL: Final = "global"


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


ATTR_STATION_ID: Final = "station_id"
ATTR_ZONE_ID: Final = "zone_id"
ATTR_DEUM_ID: Final = "deum_id"
ATTR_TIMER_ID: Final = "timer_id"
ATTR_TEMPERATURE: Final = "temperature"
ATTR_HUMIDITY: Final = "humidity"
ATTR_DEWPOINT: Final = "dewpoint"
ATTR_SETPOINT: Final = "setpoint"
ATTR_MODE: Final = "mode"
ATTR_OUTPUT: Final = "output"
ATTR_ENABLED: Final = "enabled"

