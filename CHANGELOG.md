# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project follows [Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-09-25

This release fixes several reliability bugs, brings the integration in line with
current Home Assistant guidelines and removes about a third of the code.
**All entity unique IDs are unchanged**, so existing entities, automations and
history are kept.

### ⚠️ Breaking changes

- **Minimum Home Assistant version is now 2024.12.0** (was 2024.1.0).
- **Entity display names changed.** Entities now use Home Assistant's
  `has_entity_name` naming and translated names, so a friendly name is the
  device name plus a short, translated suffix (e.g. *Living Summer comfort
  setpoint*, or *Soggiorno Setpoint comfort estate* in Italian). **Entity IDs are
  not changed** for existing installations; only the names shown in the UI are.
- The empty `switch` platform was removed (it never created any entity).

### Fixed

- **Options flow broken on recent Home Assistant versions.** The options flow
  set `config_entry` explicitly, which Home Assistant deprecated and then
  stopped supporting.
- **Changes took up to 5 minutes to show up.** Global status and timers were
  only re-read every 5 minutes (dehumidifiers every 60 s), even right after
  a change made from Home Assistant, so the season, timer slots, boost timer and
  dehumidifier override jumped back to the old value in the UI. A write now
  forces an immediate re-read of the resource it changed.
- **Stale data shown as current when the API is down.** When the zones request
  failed, entities fell back to the values captured at startup, possibly
  hours old, and never became unavailable. Now:
  - if zones or global status cannot be read, the update fails and the entities
    become *unavailable* until the API answers again;
  - if dehumidifiers or timers cannot be read, their last known values are kept
    and the request is retried on the next poll;
  - if the API is unreachable at startup, setup is retried automatically
    (`ConfigEntryNotReady`) instead of loading with no entities.
- **Timeouts were not handled.** An API timeout (`asyncio.TimeoutError`, not an
  `aiohttp.ClientError`) aborted the whole update and caused unhandled
  exceptions in the config flow. Timeouts are now handled like any other
  connection error.
- **Custom station name was overwritten.** Station-level entities re-registered
  the station device as `Alterego <station id>`, replacing the name chosen during
  setup. Renaming the station from the options now also updates the device.
- **Entities ignored the connection state.** The dehumidifier override select
  was always available; the humidity setpoint, boost timer and timer slot time
  entities also ignored failed updates. They now become unavailable with the
  rest of the integration.
- **Selecting `N/U` on an active timer slot sent `N/U hh:mm`** instead of `N/U`.
- **Selecting heat/cool on a zone in COMFORT or ECONOMY reset it to AUTO.** It
  now only changes the forcing when the zone is OFF.
- **Target temperature parsing.** A `0.0` setpoint (no active setpoint) was only
  ignored when sent as a string; numeric values are now handled too.
- **Authentication errors.** A server error (5xx) during login is no longer
  reported as "invalid credentials", and a 401 that persists after
  re-authentication is now treated as an authentication error.
- **Translations.** The options and reconfigure forms had no labels because
  their translations were in the wrong place; `strings.json` was out of date;
  the station ID form mentioned a comma-separated list of stations that was
  never supported; reconfiguring showed "Re-authentication completed" instead
  of "Reconfiguration completed".
- **Dehumidifier device model** switched between `deum` and `Deumidificatore`
  depending on which platform loaded last; it is now always `Dehumidifier`.

### Added

- **Re-authentication flow.** If the Alterego credentials stop working, Home
  Assistant shows a repair notification asking for the new password instead of
  failing silently.
- **Climate `turn_on` / `turn_off`** (`ClimateEntityFeature.TURN_ON` /
  `TURN_OFF`).
- **Clear error messages** in the UI when a change cannot be sent to the API,
  or when a summer-only setting is changed in winter.
- **Italian and English names for all entities**, including timer slots
  (*Monday slot 1* / *Lunedì fascia 1*).
- Boost timer now has a unit (minutes).
- **Test suite** (`tests/`, pytest + `pytest-homeassistant-custom-component`)
  covering setup, polling, failures, writes, config/reauth/reconfigure/options
  flows and the API client.
- **CI workflow** running hassfest, HACS validation and the tests.

### Changed

- Uses Home Assistant's shared HTTP session instead of creating its own.
- Uses `entry.runtime_data`, `_get_reauth_entry` / `_get_reconfigure_entry` and
  `async_update_reload_and_abort` instead of the older patterns.
- Uses `via_device_id` on Home Assistant 2026.8+ (the `via_device` key is
  deprecated there and will be removed in 2027.8), and still uses `via_device`
  on older versions.
- `PARALLEL_UPDATES = 1` on platforms that write to the API, to avoid
  concurrent writes to the cloud.
- Refactor: new `entity.py` with shared base classes (station, zone,
  dehumidifier, timer slot) and coordinator helpers replace code that was
  duplicated in every platform; the API client uses a single request path for
  all endpoints.
- `manifest.json`: removed the unnecessary `aiohttp` requirement (shipped with
  Home Assistant), fixed `codeowners` (`@itsjustdeepred`), added
  `issue_tracker`.
- `hacs.json`: removed keys HACS no longer uses.

## [1.1.2] - 2026-06-10

### Fixed

- Write API calls had no effect: write endpoints accept numeric IDs (`1`, `2`…)
  while read endpoints return prefixed IDs (`Z1`, `T1`, `D2`…). The letter
  prefix is now stripped before every write.

## [1.1.1] - 2026-06-10

### Fixed

- Standard Apache 2.0 LICENSE text so GitHub detects it; logo for HACS.

## [1.1.0] - 2026-06-10

### Fixed

- HVAC mode is `cool` in summer and `heat` in winter.
- Coordinator keeps global, dehumidifier and timer data between refreshes.
- Timer entities reduced from 420 to 70 (unused slots skipped), with distinct
  names per slot.
- Access token expiry is checked before each request.

## [1.0.0] - 2026-01-08

- First release.

[1.2.0]: https://github.com/itsjustdeepred/alterego/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/itsjustdeepred/alterego/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/itsjustdeepred/alterego/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/itsjustdeepred/alterego/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/itsjustdeepred/alterego/releases/tag/v1.0.0
