"""Support for PSE RCE price sensor."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PseRceCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the PSE RCE sensor from a config entry."""
    coordinator: PseRceCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PseRceSensor(coordinator, entry)])


class PseRceSensor(CoordinatorEntity[PseRceCoordinator], SensorEntity):
    """Representation of PSE RCE Price Sensor."""

    def __init__(self, coordinator: PseRceCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "PSE RCE Price Chain"
        self._attr_unique_id = f"{entry.entry_id}_rce_price_chain"
        self._attr_unit_of_measurement = "PLN/kWh"
        self._attr_icon = "mdi:currency-pln"

    @property
    def native_value(self) -> float:
        """Return the current price."""
        if self.coordinator.data:
            return self.coordinator.data.get("native_value", 0.0)
        return 0.0

    @property
    def extra_state_attributes(self) -> dict:
        """Return entity attributes containing the aligned list for EMHASS or charts."""
        if self.coordinator.data:
            return {
                "list": self.coordinator.data.get("list", []),
            }
        return {"list": []}