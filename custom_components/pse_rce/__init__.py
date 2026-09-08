"""The PSE RCE integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_HORIZON, CONF_START_FROM_MIDNIGHT, DEFAULT_HORIZON, DEFAULT_START_FROM_MIDNIGHT, DOMAIN
from .coordinator import PseRceCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PSE RCE from a config entry."""
    horizon = entry.options.get(CONF_HORIZON, entry.data.get(CONF_HORIZON, DEFAULT_HORIZON))
    start_from_midnight = entry.options.get(
        CONF_START_FROM_MIDNIGHT, entry.data.get(CONF_START_FROM_MIDNIGHT, DEFAULT_START_FROM_MIDNIGHT)
    )

    coordinator = PseRceCoordinator(hass, horizon, start_from_midnight)
    await coordinator.async_config_entry_first_refresh()

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