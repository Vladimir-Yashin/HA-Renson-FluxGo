# Renson Flux Go for Home Assistant

A local Home Assistant integration for Renson Flux Go ventilation units.

This is a fork of https://github.com/KNSd2/HA-renson-flux that supports Renson Flux, but not Renson Flux Go units.

## Entities

I try to report as many entities from http://<ip>/service/sensor-data and /service/device-state pages.
Few notes:
- **Active Mode** shows **Boost** when either fan's boost is enabled and includes each fan's level and remaining time as attributes. Otherwise it shows **No boost**.
- **CO2 Level**, **VOC Level** are not reported. My unit doesn't have this sensor.

The integration sends the fixed `X-API-Service-Key` value observed in the Flux Go Wall 400 running v2.8.2 ;this value may change in other firmware versions.

## Services

- `renson_fluxgo.set_boost`: Set extract and supply boost at `speed` percent for `timer` minutes. The duration can be very long. 8-10 hours works fine.

Example Home Assistant service call for eight quiet hours:

```yaml
action: renson_fluxgo.set_boost
data:
  speed: 20
  timer: 480
```

- Revert to full auto mode by setting boost of 1 minute.


## Installation

1. Install as a custom repository in HACS.
2. Configure the unit's IP address and API key in **Settings → Devices & Services → Add Integration**.

Setup creates one **Renson Flux Go (<IP address>)** device containing all 16 sensor entities, with a link to the unit's web interface.

The API key is printed in the leaflet delivered with the unit.
Another way to get it is to visit Flux Go web UI, wait for it to ask you to press a button on it, then pass the authentication. X-API-Key HTTP header will now be sent in every HTTP request. Use your browser's dev tools console to inspect the requests.

That's the key you need.

## API features not exposed yet

Some other API features are not exposed.
Use web interface for those.

Renson Ventilation app allows to set an operating mode (Eco/Health/Intense) with their distinct curves.
It also supports a manual mode.
The problem is that it "talks" to the Flux Go unit via an Azure-hosted API.

I don't have the docs for the local API and frankly, IMO, 99% of the features boil down to monitoring, set_boost and a set of rules you can make in HomeAssistant. 
