"""Renson Flux Go integration."""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import FluxGoApi

DOMAIN = "renson_fluxgo"
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        **entry.data,
        "api": FluxGoApi(entry.data["host"], entry.data["api_key"]),
        "command_lock": asyncio.Lock(),
    }

    async def run_command(method, *args):
        async with hass.data[DOMAIN][entry.entry_id]["command_lock"]:
            future = hass.async_add_executor_job(method, *args)
            try:
                return await asyncio.shield(future)
            except asyncio.CancelledError:
                # The executor request keeps running after coroutine cancellation.
                # Wait for it so the next service cannot be overwritten by it.
                await future
                raise

    async def refresh():
        data = hass.data[DOMAIN][entry.entry_id]
        for key in ("sensor_coordinator", "status_coordinator"):
            if coordinator := data.get(key):
                await coordinator.async_request_refresh()
        for entity in data.get("status_entities", []):
            await entity.async_update_ha_state(force_refresh=True)

    async def set_boost(call):
        speed = int(call.data.get("speed", 100))
        minutes = int(call.data.get("timer", 30))
        await run_command(
            hass.data[DOMAIN][entry.entry_id]["api"].set_boost, speed, minutes
        )
        await refresh()

    # Home Assistant services are global. Register once; an optional host routes
    # commands when more than one Flux Go unit is configured.
    if not hass.services.has_service(DOMAIN, "set_boost"):
        async def dispatch(service_name, call):
            host = call.data.get("host")
            entries = hass.data[DOMAIN]
            matches = [item for item in entries.values() if host is None or item["host"] == host]
            if len(matches) != 1:
                raise ValueError("Specify host when multiple Renson Flux Go units are configured")
            target_id = next(key for key, item in entries.items() if item is matches[0])
            handler = entries[target_id]["handlers"][service_name]
            await handler(call)

        for service_name in ("set_boost",):
            async def handle(call, name=service_name):
                await dispatch(name, call)
            hass.services.async_register(DOMAIN, service_name, handle)

    hass.data[DOMAIN][entry.entry_id]["handlers"] = {
        "set_boost": set_boost,
    }
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "set_boost")
    return unloaded
