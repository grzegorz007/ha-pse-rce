"""The PSE RCE integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_HORIZON, 
    CONF_START_FROM_MIDNIGHT, 
    CONF_RESOLUTION,
    CONF_FALLBACK_STRATEGY,
    CONF_CLAMP_NEGATIVE,
    CONF_PRICE_FACTOR,
    CONF_PRICE_OFFSET,
    DEFAULT_HORIZON, 
    DEFAULT_START_FROM_MIDNIGHT, 
    DEFAULT_RESOLUTION,
    DEFAULT_FALLBACK_STRATEGY,
    DEFAULT_CLAMP_NEGATIVE,
    DEFAULT_PRICE_FACTOR,
    DEFAULT_PRICE_OFFSET,
    DOMAIN
)
from .coordinator import PseRceCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PSE RCE from a config entry."""
    opts = entry.options
    data = entry.data

    horizon = opts.get(CONF_HORIZON, data.get(CONF_HORIZON, DEFAULT_HORIZON))
    start_from_midnight = opts.get(
        CONF_START_FROM_MIDNIGHT, data.get(CONF_START_FROM_MIDNIGHT, DEFAULT_START_FROM_MIDNIGHT)
    )
    resolution = opts.get(
        CONF_RESOLUTION, data.get(CONF_RESOLUTION, DEFAULT_RESOLUTION)
    )
    fallback_strategy = opts.get(
        CONF_FALLBACK_STRATEGY, data.get(CONF_FALLBACK_STRATEGY, DEFAULT_FALLBACK_STRATEGY)
    )
    clamp_negative_prices = opts.get(
        CONF_CLAMP_NEGATIVE, data.get(CONF_CLAMP_NEGATIVE, DEFAULT_CLAMP_NEGATIVE)
    )
    price_factor = float(
        opts.get(CONF_PRICE_FACTOR, data.get(CONF_PRICE_FACTOR, DEFAULT_PRICE_FACTOR))
    )
    price_offset = float(
        opts.get(CONF_PRICE_OFFSET, data.get(CONF_PRICE_OFFSET, DEFAULT_PRICE_OFFSET))
    )

    coordinator = PseRceCoordinator(
        hass=hass, 
        horizon_hours=horizon, 
        start_from_midnight=start_from_midnight, 
        resolution=resolution, 
        fallback_strategy=fallback_strategy,
        clamp_negative_prices=clamp_negative_prices,
        price_factor=price_factor,
        price_offset=price_offset,
    )
    
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Błąd podczas pierwszego pobierania danych PSE RCE: %s", err)
        raise ConfigEntryNotReady(f"Nie można pobrać danych PSE RCE: {err}") from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)