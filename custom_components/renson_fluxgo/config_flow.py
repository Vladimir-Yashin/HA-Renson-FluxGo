"""Config flow for Renson Flux Go."""

import requests
import voluptuous as vol
from homeassistant import config_entries

from . import DOMAIN
from .api import FluxGoApi

DATA_SCHEMA = vol.Schema({
    vol.Required("host", default="192.168.1.11"): str,
    vol.Required("api_key"): str,
})


def test_connection(host, api_key):
    try:
        FluxGoApi(host, api_key).verify_token()
        return True
    except requests.RequestException:
        return False


class RensonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            valid = await self.hass.async_add_executor_job(
                test_connection, user_input["host"], user_input["api_key"]
            )
            if valid:
                await self.async_set_unique_id(user_input["host"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Renson Flux Go", data=user_input)
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
