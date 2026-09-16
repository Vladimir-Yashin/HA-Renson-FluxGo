# Renson Flux Go for Home Assistant

A local Home Assistant integration for Renson Flux Go ventilation units. Configure the unit's IP address and API key in **Settings → Devices & Services → Add Integration**. Pairing or “knock” is outside this integration.

The integration uses the HTTP endpoints observed on a Flux Go 400 Wall with firmware 2.8.2. See [API_SPEC.md](API_SPEC.md) for the captured API details. Your unit must be reachable from Home Assistant on its local network.

## Entities

- **Active Mode** shows **Boost** when either fan's boost is enabled and includes each fan's level and remaining time as attributes. Otherwise it shows **No boost**. The captured API does not expose an automatic/manual mode enum.
- **Breeze Status** reads `/api/v1/decision/status`.
- **CO2 Level**, **VOC Level**, and **Humidity Level** read `indoor_co2`, `indoor_voc`, and `relative_humidity`. Missing optional sensors show an unavailable value.
- **Exhaust and Supply Fan Flow Rate, Power, and RPM** show airflow in m³/h, electrical power in W, and fan speed in rpm.
- **Exhaust, Indoor, Intake, and Outdoor Temperature** show temperatures in °C.

All numeric sensors above share one `/api/v1/decision/sensor_values` request every 15 minutes and refresh after a boost command. The observed browser call included an additional `x-api-service-key` whose source is unknown. This integration uses the configured API key only. If the unit requires the service key, these sensors will be unavailable until its access method is known.

## Services

- `renson_fluxgo.set_boost`: Set extract and supply boost at `speed` percent for `timer` minutes. The duration can be as long as 10 hours (`timer: 600`). For several quiet hours, choose a low level and set `timer` to the number of hours multiplied by 60. For example, `speed: 20` and `timer: 480` requests eight hours at 20%.

Example Home Assistant service call for eight quiet hours:

```yaml
action: renson_fluxgo.set_boost
data:
  speed: 20
  timer: 480
```

There are no separate minimum, automatic, or sleep services. The API client has a `clear_boost()` helper for ending a boost early; it is not exposed as a Home Assistant service.

The service domain is `renson_fluxgo`. If multiple units are configured, provide the optional `host` field to select one. A boost writes extract and supply separately; if one request fails, the other may still have changed.

## Installation

Copy `custom_components/renson_fluxgo` into your Home Assistant configuration's `custom_components` directory and restart Home Assistant. Then add **Renson Flux Go** from **Settings → Devices & Services** and enter the local IP address and API key.

## API features not exposed yet

The API also reports supply temperature, absolute humidity, fan pressure, filter lifetime, current errors, bypass and frost protection status, and device details. Filter lifetime and bypass status look particularly useful as additional sensors. Profile, program, silent schedule, and protection settings are available in the decision tree but are not exposed as controls because their write behavior was not captured.
