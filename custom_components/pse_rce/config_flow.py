"""Config flow for PSE RCE integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_CLAMP_NEGATIVE,
    CONF_FALLBACK_STRATEGY,
    CONF_HORIZON,
    CONF_PRICE_FACTOR,
    CONF_PRICE_OFFSET,
    CONF_RESOLUTION,
    CONF_START_FROM_MIDNIGHT,
    DEFAULT_CLAMP_NEGATIVE,
    DEFAULT_FALLBACK_STRATEGY,
    DEFAULT_HORIZON,
    DEFAULT_PRICE_FACTOR,
    DEFAULT_PRICE_OFFSET,
    DEFAULT_RESOLUTION,
    DEFAULT_START_FROM_MIDNIGHT,
    DOMAIN,
)


def _schema(defaults: dict) -> vol.Schema:
    """Build the shared configuration schema."""
    return vol.Schema(
        {
            vol.Required(CONF_HORIZON, default=defaults[CONF_HORIZON]): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=48)
            ),
            vol.Required(
                CONF_START_FROM_MIDNIGHT, default=defaults[CONF_START_FROM_MIDNIGHT]
            ): bool,
            vol.Required(CONF_RESOLUTION, default=defaults[CONF_RESOLUTION]): vol.In(
                ["15m", "30m"]
            ),
            vol.Required(
                CONF_FALLBACK_STRATEGY, default=defaults[CONF_FALLBACK_STRATEGY]
            ): vol.In(["last", "repeat", "zero"]),
            vol.Required(
                CONF_CLAMP_NEGATIVE, default=defaults[CONF_CLAMP_NEGATIVE]
            ): bool,
            vol.Required(CONF_PRICE_FACTOR, default=defaults[CONF_PRICE_FACTOR]): vol.All(
                vol.Coerce(float), vol.Range(min=0)
            ),
            vol.Required(CONF_PRICE_OFFSET, default=defaults[CONF_PRICE_OFFSET]): vol.Coerce(
                float
            ),
        }
    )


class PseRceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PSE RCE."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title="PSE RCE Prices",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(
                {
                    CONF_HORIZON: DEFAULT_HORIZON,
                    CONF_START_FROM_MIDNIGHT: DEFAULT_START_FROM_MIDNIGHT,
                    CONF_RESOLUTION: DEFAULT_RESOLUTION,
                    CONF_FALLBACK_STRATEGY: DEFAULT_FALLBACK_STRATEGY,
                    CONF_CLAMP_NEGATIVE: DEFAULT_CLAMP_NEGATIVE,
                    CONF_PRICE_FACTOR: DEFAULT_PRICE_FACTOR,
                    CONF_PRICE_OFFSET: DEFAULT_PRICE_OFFSET,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return PseRceOptionsFlowHandler()


class PseRceOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for PSE RCE."""

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

        defaults = {
            CONF_HORIZON: horizon,
            CONF_START_FROM_MIDNIGHT: start_from_midnight,
            CONF_RESOLUTION: self.config_entry.options.get(
                CONF_RESOLUTION,
                self.config_entry.data.get(CONF_RESOLUTION, DEFAULT_RESOLUTION),
            ),
            CONF_FALLBACK_STRATEGY: self.config_entry.options.get(
                CONF_FALLBACK_STRATEGY,
                self.config_entry.data.get(CONF_FALLBACK_STRATEGY, DEFAULT_FALLBACK_STRATEGY),
            ),
            CONF_CLAMP_NEGATIVE: self.config_entry.options.get(
                CONF_CLAMP_NEGATIVE,
                self.config_entry.data.get(CONF_CLAMP_NEGATIVE, DEFAULT_CLAMP_NEGATIVE),
            ),
            CONF_PRICE_FACTOR: self.config_entry.options.get(
                CONF_PRICE_FACTOR,
                self.config_entry.data.get(CONF_PRICE_FACTOR, DEFAULT_PRICE_FACTOR),
            ),
            CONF_PRICE_OFFSET: self.config_entry.options.get(
                CONF_PRICE_OFFSET,
                self.config_entry.data.get(CONF_PRICE_OFFSET, DEFAULT_PRICE_OFFSET),
            ),
        }

        return self.async_show_form(step_id="init", data_schema=_schema(defaults))