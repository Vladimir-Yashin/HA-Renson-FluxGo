"""Sensors for Renson Flux Go."""

import logging
from datetime import timedelta

import requests
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=15)
WHOLE_NUMBER_FIELDS = (
    "relative_humidity",
    "absolute_humidity",
    "exhaust_fan_flow_rate",
    "supply_fan_flow_rate",
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    config = hass.data[DOMAIN][entry.entry_id]
    api = config["api"]
    host = config["host"]

    async def async_update_values():
        try:
            return await hass.async_add_executor_job(api.get, "/decision/sensor_values")
        except (requests.RequestException, ValueError) as exc:
            raise UpdateFailed(f"Cannot read Flux Go sensor values: {exc}") from exc

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"Renson Flux Go {host} sensor values",
        update_method=async_update_values,
        update_interval=SCAN_INTERVAL,
    )
    config["sensor_coordinator"] = coordinator
    await coordinator.async_refresh()

    value_entities = [
        FluxGoSensor(coordinator, entry, "relative_humidity", "Humidity (relative) indoor", "mdi:water-percent", "%"),
        FluxGoSensor(coordinator, entry, "absolute_humidity", "Humidity (absolute) indoor", "mdi:water-percent", "g/kg"),
        FluxGoSensor(coordinator, entry, "exhaust_fan_flow_rate", "Flow rate exhaust", "mdi:fan", "m³/h"),
        FluxGoSensor(coordinator, entry, "exhaust_fan_power", "Power of exhaust fan", "mdi:flash", "W", SensorDeviceClass.POWER),
        FluxGoSensor(coordinator, entry, "exhaust_fan_rpm", "RPM exhaust fan", "mdi:fan", "rpm"),
        FluxGoSensor(coordinator, entry, "supply_fan_flow_rate", "Flow rate supply", "mdi:fan", "m³/h"),
        FluxGoSensor(coordinator, entry, "supply_fan_power", "Power of supply fan", "mdi:flash", "W", SensorDeviceClass.POWER),
        FluxGoSensor(coordinator, entry, "supply_fan_rpm", "RPM supply fan", "mdi:fan", "rpm"),
        FluxGoSensor(coordinator, entry, "indoor_temperature", "Extract air temperature (ETA)", "mdi:thermometer", "°C", SensorDeviceClass.TEMPERATURE),
        FluxGoSensor(coordinator, entry, "outdoor_temperature", "Outdoor air temperature (ODA)", "mdi:thermometer", "°C", SensorDeviceClass.TEMPERATURE),
        FluxGoSensor(coordinator, entry, "exhaust_temperature", "Exhaust air temperature (EHA)", "mdi:thermometer", "°C", SensorDeviceClass.TEMPERATURE),
        FluxGoSensor(coordinator, entry, "supply_temperature", "Supply air temperature (SUP)", "mdi:thermometer", "°C", SensorDeviceClass.TEMPERATURE),
        
    ]
    status_entities = [
        FluxGoModeSensor(api, entry),
        FluxGoBreezeSensor(api, entry),
        FluxGoFilterLifetimeSensor(api, entry),
    ]
    config["status_entities"] = status_entities
    async_add_entities(value_entities)
    async_add_entities(status_entities, True)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    """Describe the single ventilation unit belonging to this config entry."""
    host = entry.data["host"]
    return DeviceInfo(
        # Use the config entry identity; the IP address and API key can change.
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Renson Flux Go ({host})",
        manufacturer="Renson",
        model="Flux Go",
        configuration_url=f"http://{host}",
    )


class FluxGoBaseSensor(SensorEntity):
    def __init__(self, api, entry: ConfigEntry, key, name, icon):
        host = entry.data["host"]
        self._attr_device_info = _device_info(entry)
        self.api = api
        self._attr_name = f"Renson Flux Go {name}"
        self._attr_icon = icon
        self._attr_unique_id = f"renson_flux_{host}_{key}"
        self._attr_native_value = None

    def read(self, path):
        try:
            self._attr_available = True
            return self.api.get(path)
        except (requests.RequestException, ValueError) as exc:
            self._attr_available = False
            _LOGGER.warning("Cannot read Renson Flux Go %s: %s", path, exc)
            return None


class FluxGoSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry: ConfigEntry, field, name, icon, unit=None, device_class=None):
        super().__init__(coordinator)
        host = entry.data["host"]
        self._attr_device_info = _device_info(entry)
        # Preserve unique IDs for existing Home Assistant entity registry entries.
        key = {"indoor_co2": "co2", "indoor_voc": "voc", "relative_humidity": "humidity"}.get(field, field)
        self._attr_name = f"Renson Flux Go {name}"
        self._attr_icon = icon
        self._attr_unique_id = f"renson_flux_{host}_{key}"
        self.field = field
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        if field not in ("indoor_co2", "indoor_voc", "relative_humidity"):
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        value = self.coordinator.data.get(self.field) if self.coordinator.data else None
        if value is not None and self.field in WHOLE_NUMBER_FIELDS:
            return round(value)
        return value


class FluxGoModeSensor(FluxGoBaseSensor):
    def __init__(self, api, entry: ConfigEntry):
        super().__init__(api, entry, "mode", "Active Mode", "mdi:fan")

    def update(self):
        data = self.read("/decision")
        if data is None:
            return
        room = data.get("room", {}).get("0", {})
        extract = room.get("extract", {}).get("boost", {})
        supply = room.get("supply", {}).get("boost", {})
        enabled = [boost for boost in (extract, supply) if boost.get("enable")]
        if enabled:
            self._attr_native_value = "Boost"
            self._attr_extra_state_attributes = {
                "extract_level": extract.get("level") if extract.get("enable") else None,
                "supply_level": supply.get("level") if supply.get("enable") else None,
                "extract_remaining_seconds": extract.get("remaining"),
                "supply_remaining_seconds": supply.get("remaining"),
            }
        else:
            self._attr_native_value = "No boost"
            self._attr_extra_state_attributes = {}


class FluxGoBreezeSensor(FluxGoBaseSensor):
    def __init__(self, api, entry: ConfigEntry):
        super().__init__(api, entry, "breeze", "Breeze Status", "mdi:weather-windy")

    def update(self):
        data = self.read("/decision/status")
        if data is not None:
            self._attr_native_value = data.get("breeze", "unknown").title()


class FluxGoFilterLifetimeSensor(FluxGoBaseSensor):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, api, entry: ConfigEntry):
        super().__init__(
            api, entry, "filter_current_lifetime", "Filter change in (days)", "mdi:air-filter"
        )

    def update(self):
        hours = self.read("/filter/current_lifetime")
        self._attr_native_value = hours // 24 if hours is not None else None
