<div align="center">

![Alterego Logo](https://raw.githubusercontent.com/itsjustdeepred/alterego/main/logo.png)

# Alterego Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]
[![hacs][hacs-shield]][hacs]
[![Maintainer][maintainer-shield]][maintainer]

[![Open your Home Assistant instance and show the integrations page.][my-ha-badge]][my-ha]
[![Open your Home Assistant instance and show the add integration page.][add-integration-badge]][add-integration]

</div>

> **⚠️ Disclaimer**: This integration is **not official** and is **not affiliated with or endorsed by** Alterego or its manufacturers. This is an independent, community-developed integration.

Home Assistant integration for Alterego climate control systems (radiant floor, fan coil, VMC/dehumidifiers). Supports monitoring and full control of zones, timers, and dehumidifiers via the Alterego cloud API.

## Features

- **GUI Configuration**: Set up via the Home Assistant UI — no YAML editing required
- **Station Selection**: Choose from all available stations after login
- **Zone Monitoring**: Temperature, humidity, and dewpoint sensors per zone
- **Seasonal Climate Control**: Zones switch automatically between `cool` (summer) and `heat` (winter) mode based on the configured season
- **Forcing Modes**: Override each zone to AUTO / COMFORT / ECONOMY / OFF
- **Setpoints**: Set comfort and economy setpoints independently for summer and winter
- **Dehumidifier / VMC Control**: Override speed (AUTO, LOW, MEDIUM, HIGH, OFF) for each visible dehumidifier or VMC unit
- **Timer Programming**: Weekly schedule control — mode and time for each active daily slot
- **Season Select**: Switch the whole system between SUMMER and WINTER from Home Assistant
- **Efficient Polling**: Zones every 30 s, global status every 5 min, timers and dehumidifiers every 5 min

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three dots (top right) → **Custom repositories**
4. Add `https://github.com/itsjustdeepred/alterego` — category: **Integration**
5. Find **Alterego** in the list and click **Download**
6. Restart Home Assistant
7. Go to **Settings → Devices & Services → Add Integration**, search for **Alterego**

### Manual Installation

1. Copy the `custom_components/cappellotto` folder into your HA `custom_components` directory
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration**, search for **Alterego**

## Configuration

| Parameter | Required | Description |
|-----------|----------|-------------|
| Email | Yes | Alterego account email |
| Password | Yes | Alterego account password |
| Station | Yes | Select from the list of available stations |
| Station Name | No | Optional custom display name (defaults to station ID) |

To update credentials or station name after setup: go to the integration page and click **Configure**.

## Entities

### Sensors
| Entity | Unit | Notes |
|--------|------|-------|
| Zone Temperature | °C | All enabled zones |
| Zone Humidity | % | Zones with T+RH sensor |
| Zone Dewpoint | °C | Zones with T+RH sensor |
| Outside Temperature | °C | From the station |
| Global Status | — | System on/off state, season, last connection |

### Climate
One entity per enabled zone.

| Feature | Details |
|---------|---------|
| HVAC mode | `cool` in summer · `heat` in winter · `off` |
| Preset modes | AUTO · COMFORT · ECONOMY · OFF |
| Target temperature | Reads and writes the active seasonal setpoint |
| Min / Max temp | Read from global station parameters per season |

### Select
| Entity | Options |
|--------|---------|
| Zone Forcing | AUTO · COMFORT · ECONOMY · OFF |
| Dehumidifier / VMC Override | AUTO · LOW · MEDIUM · HIGH · OFF |
| Season | SUMMER · WINTER |
| Timer slot mode (per active slot) | COMFORT · ECONOMY · OFF |

### Number
| Entity | Notes |
|--------|-------|
| Zone Comfort Setpoint Summer | °C |
| Zone Economy Setpoint Summer | °C |
| Zone Comfort Setpoint Winter | °C |
| Zone Economy Setpoint Winter | °C |
| Zone Humidity Setpoint | % — available in summer only |
| Dehumidifier Boost Timer | min — available in summer only |

### Time
Timer slot start time for each active slot (Fascia 1, Fascia 2…) per day of the week. Inactive slots (N/U) are hidden.

## Troubleshooting

**Entities not appearing** — wait a few minutes after first setup; check HA logs for API errors.

**Authentication errors** — verify email and password; ensure your Alterego account has an active station.

**HACS: "unable to select next github token from pool"** — configure a GitHub Personal Access Token in HACS settings (HACS → three dots → Settings → GitHub token).

## Requirements

- Home Assistant 2024.1.0 or later
- Alterego account with at least one active station
- Python package `aiohttp >= 3.8.0` (installed automatically)

## Disclaimer

This is an **unofficial, community-developed** project — not created, maintained, or endorsed by Alterego or its manufacturers. Provided as-is, use at your own risk.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

---

<div align="center">

**Found this useful? Leave a ⭐ on GitHub!**

</div>

[releases-shield]: https://img.shields.io/github/release/itsjustdeepred/alterego.svg
[releases]: https://github.com/itsjustdeepred/alterego/releases
[license-shield]: https://img.shields.io/github/license/itsjustdeepred/alterego.svg
[license]: https://github.com/itsjustdeepred/alterego/blob/main/LICENSE
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs]: https://hacs.xyz
[maintainer-shield]: https://img.shields.io/badge/maintainer-@itsjustdeepred-blue.svg
[maintainer]: https://github.com/itsjustdeepred
[my-ha-badge]: https://my.home-assistant.io/badges/integrations.svg
[my-ha]: https://my.home-assistant.io/redirect/integrations/
[add-integration-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
[add-integration]: https://my.home-assistant.io/redirect/config_flow_start/?domain=cappellotto
[repository]: https://github.com/itsjustdeepred/alterego
