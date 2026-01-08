<div align="center">

![Cappellotto Logo](logo_cappellotto.png)

# Alterego Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]
[![hacs][hacs-shield]][hacs]
[![Maintainer][maintainer-shield]][maintainer]

[![Open your Home Assistant instance and show the integrations page.][my-ha-badge]][my-ha]
[![Open your Home Assistant instance and show the add integration page.][add-integration-badge]][add-integration]

</div>

> **⚠️ Disclaimer**: This integration is **not official** and is **not affiliated with or endorsed by** Alterego or its manufacturers. This is an independent, community-developed integration.

Enhanced Alterego integration for Home Assistant with GUI-based configuration flow, station selection, and comprehensive control capabilities.

## Features

* **GUI Configuration**: Set up the integration through the Home Assistant UI without editing YAML files
* **Station Selection**: Choose from available stations after authentication
* **Zone Monitoring**: Track temperature, humidity, and dewpoint for each zone
* **Climate Control**: Manage zone setpoints (comfort/economy, summer/winter) with forcing modes
* **Dehumidifier Management**: Control dehumidifiers with override modes (AUTO, LOW, MEDIUM, HIGH, OFF)
* **Timer Programming**: Configure weekly schedules with multiple time slots per day
* **Real-time Updates**: Uses a data coordinator for efficient polling and updates
* **Reconfiguration**: Update credentials and station name without removing and re-adding the integration

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to Integrations
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/itsjustdeepred/alterego`
6. Select category: "Integration"
7. Click "Add"
8. Find "Alterego" in the HACS integrations list
9. Click "Download"
10. Restart Home Assistant
11. Go to Settings → Devices & Services → Add Integration
12. Search for "Alterego" and follow the setup wizard

### Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/cappellotto` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration
5. Search for "Alterego" and follow the setup wizard

## Configuration

### Setup Steps

1. **Add Integration in Home Assistant**:
   * Go to Settings → Devices & Services → Add Integration
   * Search for "Alterego"
   * Enter your Alterego account email (username)
   * Enter your password
   * Select your station from the list
   * Optionally set a custom local name for the station
   * Complete the setup

2. **Entities Created**:
   * **Sensors**: Temperature, humidity, and dewpoint for each zone
   * **Climate**: Zone temperature control with setpoints
   * **Select**: Zone forcing modes, dehumidifier overrides, season selection
   * **Number**: Zone setpoints (comfort/economy, summer/winter)
   * **Time**: Timer slot time configuration

### Reconfiguration

To update your credentials or station name:

1. Go to Settings → Devices & Services
2. Find your Alterego integration
3. Click on it, then click "Configure"
4. Update your username, password, or station name
5. Changes take effect after reload

## Supported Entities

### Sensors
* **Temperature**: Current temperature for each zone
* **Humidity**: Current humidity for zones with T+RH sensors
* **Dewpoint**: Dewpoint temperature for zones with T+RH sensors
* **Outside Temperature**: External temperature sensor
* **Global Status**: System status and connection information

### Climate
* Zone temperature control
* Summer/winter setpoints (comfort and economy)
* Forcing modes: AUTO, OFF, ECONOMY, COMFORT

### Select
* **Zone Forcing Mode**: AUTO, OFF, ECONOMY, COMFORT
* **Dehumidifier Override**: AUTO, LOW, MEDIUM, HIGH, OFF
* **Season**: SUMMER, WINTER
* **Timer Slots**: Mode selection for each timer slot

### Number
* Zone setpoints (summer/winter, comfort/economy)
* Humidity setpoint
* Dehumidifier boost timer

### Time
* Timer slot time configuration (all 6 slots for all 7 days)

## Troubleshooting

### Authentication Issues

* Verify your email and password are correct
* Check that your Alterego account is active
* Ensure your station is accessible

### Entities Not Appearing

* Wait a few minutes after setup for initial data fetch
* Check Home Assistant logs for any errors
* Verify your station has enabled zones

### API Rate Limiting

* The integration automatically respects API rate limits
* Updates are staggered to avoid exceeding limits
* If you see rate limit errors, wait a few minutes

## Requirements

* Home Assistant 2024.1.0 or later
* Alterego account with active station
* Python package: `aiohttp>=3.8.0` (installed automatically)

## Disclaimer

This integration is an **unofficial, community-developed** project. It is:
* **Not** created, maintained, or supported by Alterego
* **Not** affiliated with or endorsed by Alterego or its manufacturers
* Provided "as-is" without any warranty

Use at your own risk. The developers are not responsible for any issues or damages that may arise from using this integration.

## Support

For issues, feature requests, or contributions, please visit the [GitHub repository][repository].

## License

This project is licensed under the Apache License 2.0\. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

**If you find this integration useful, please consider giving it a ⭐ on GitHub!**

Made with ❤️ for the Home Assistant community

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
