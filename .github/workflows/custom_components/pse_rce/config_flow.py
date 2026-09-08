"""Config flow for PSE RCE integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_HORIZON, CONF_START_FROM_MIDNIGHT, DEFAULT_HORIZON, DEFAULT_START_FROM_MIDNIGHT, DOMAIN


class PseRceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PSE RCE."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(
                title="PSE RCE Prices",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_HORIZON, default=DEFAULT_HORIZON): int,
                vol.Required(CONF_START_FROM_MIDNIGHT, default=DEFAULT_START_FROM_MIDNIGHT): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return PseRceOptionsFlowHandler(config_entry)


class PseRceOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for PSE RCE."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        horizon = self.config_entry.options.get(
            CONF_HORIZON, self.config_entry.data.get(CONF_HORIZON, DEFAULT_HORIZON)
        )
        start_from_midnight = self.config_entry.options.get(
            CONF_START_FROM_MIDNIGHT,
            self.config_entry.data.get(CONF_START_FROM_MIDNIGHT, DEFAULT_START_FROM_MIDNIGHT),
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_HORIZON, default=horizon): int,
                vol.Required(CONF_START_FROM_MIDNIGHT, default=start_from_midnight): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)