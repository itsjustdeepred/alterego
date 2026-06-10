# Alterego Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]
[![hacs][hacsbadge]][hacs]
[![Maintainer][maintainer-shield]][maintainer]

<p align="center">
  <img width="320" src="https://raw.githubusercontent.com/itsjustdeepred/alterego/main/logo.png">
</p>

> **⚠️ Disclaimer**: This integration is **not official** and is **not affiliated with or endorsed by** Alterego or its manufacturers.

Home Assistant integration for Alterego climate control systems (radiant floor, fan coil, VMC/dehumidifiers). Requires an Alterego account with at least one active station.

## Setup

Go to **Settings → Devices & Services → Add Integration**, search for **Alterego** and enter:

| Parameter | Required | Description |
|-----------|----------|-------------|
| Email | Yes | Alterego account email |
| Password | Yes | Alterego account password |
| Station | Yes | Select from the list of available stations |
| Station Name | No | Optional custom display name |

## What gets created

**Sensors** — temperature, humidity (T+RH zones), dewpoint (T+RH zones), outside temperature, global status.

**Climate** — one entity per zone: `cool` in summer · `heat` in winter · `off`. Presets: AUTO / COMFORT / ECONOMY / OFF. Setpoint reads and writes the correct seasonal value automatically.

**Select** — zone forcing mode, dehumidifier/VMC override, season (SUMMER/WINTER), timer slot mode per active slot.

**Number** — comfort and economy setpoints for summer and winter; humidity setpoint and dehumidifier boost timer (summer only).

**Time** — start time for each active timer slot (Fascia 1, Fascia 2…) per day of the week.

## Update intervals

- Zones: every 30 s
- Global status / Timers: every 5 min
- Dehumidifiers: every 5 min

Minimum required Home Assistant version: **2024.1.0**

---

[releases-shield]: https://img.shields.io/github/release/itsjustdeepred/alterego.svg?style=flat-square
[releases]: https://github.com/itsjustdeepred/alterego/releases
[license-shield]: https://img.shields.io/github/license/itsjustdeepred/alterego.svg?style=flat-square
[license]: https://github.com/itsjustdeepred/alterego/blob/main/LICENSE
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square
[maintainer-shield]: https://img.shields.io/badge/maintainer-@itsjustdeepred-blue.svg?style=flat-square
[maintainer]: https://github.com/itsjustdeepred
