# Alterego Integration for Home Assistant

Enhanced Alterego integration for Home Assistant with GUI-based configuration flow, station selection, and comprehensive control capabilities.

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]
[![hacs][hacsbadge]][hacs]
[![Maintainer][maintainer-shield]][maintainer]

<p align="center">
  <img width="360" src="logo_cappellotto.png">
</p>

> **⚠️ Disclaimer**: This integration is **not official** and is **not affiliated with or endorsed by** Alterego or its manufacturers. This is an independent, community-developed integration.

This integration adds support for controlling and monitoring Alterego home temperature and VMC (Ventilation Mechanical Control) systems through the Alterego cloud API. It provides a GUI-based configuration flow that allows you to select your station and manage all aspects of your system.

For this integration you **must have an Alterego account** with an active station.

## Features

- **GUI Configuration**: Set up the integration through the Home Assistant UI without editing YAML files
- **Station Selection**: Choose from available stations after authentication
- **Zone Monitoring**: Track temperature, humidity, and dewpoint for each zone
- **Climate Control**: Manage zone setpoints (comfort/economy, summer/winter) with forcing modes
- **Dehumidifier Management**: Control dehumidifiers with override modes (AUTO, LOW, MEDIUM, HIGH, OFF)
- **Timer Programming**: Configure weekly schedules with multiple time slots per day
- **Real-time Updates**: Uses a data coordinator for efficient polling and updates
- **Reconfiguration**: Update credentials and station name without removing and re-adding the integration

## Configuration

To add Alterego to your installation, do the following:

- Go to Settings → Devices & Services
- Click the + ADD INTEGRATION button in the lower right corner
- Search for **Alterego** and click the integration
- When loaded, there will be a configuration box, where you must enter:

  | Parameter | Required | Default Value | Description |
  | --------- | -------- | ------------- | ----------- |
  | `Email` | Yes | None | Your Alterego account email (username) |
  | `Password` | Yes | None | Your Alterego account password |
  | `Station` | Yes | None | Select your station from the list of available stations |
  | `Station Name` | No | Station ID | Optional custom local name for the station |

- Click on SUBMIT to save your data
- The integration will automatically create entities for all enabled zones, dehumidifiers, and timers

**Important**: This is an **unofficial integration** and is **not affiliated with or endorsed by** Alterego or its manufacturers.

Minimum required version of Home Assistant is **2024.1.0**.

***

[releases-shield]: https://img.shields.io/github/release/itsjustdeepred/alterego.svg?style=flat-square
[releases]: https://github.com/itsjustdeepred/alterego/releases
[license-shield]: https://img.shields.io/github/license/itsjustdeepred/alterego.svg?style=flat-square
[license]: https://github.com/itsjustdeepred/alterego/blob/main/LICENSE
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square
[maintainer-shield]: https://img.shields.io/badge/maintainer-@itsjustdeepred-blue.svg?style=flat-square
[maintainer]: https://github.com/itsjustdeepred
