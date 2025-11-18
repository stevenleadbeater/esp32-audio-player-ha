"""Config flow for ESP32 Audio Player integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_DEVICE_ID

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="Living Room Speaker"): str,
        vol.Required(CONF_DEVICE_ID, default="esp32-audio-01"): str,
        vol.Required(CONF_HOST, default="192.168.1.175"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ESP32 Audio Player."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Set unique ID based on device_id
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
