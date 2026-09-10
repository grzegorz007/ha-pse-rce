"""Sensor platform for PSE RCE."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PseRceCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PSE RCE sensors based on a config entry."""
    coordinator: PseRceCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            PseRcePriceChainSensor(coordinator, entry),
            PseRceTodayMinPriceSensor(coordinator, entry),
            PseRceTodayMaxPriceSensor(coordinator, entry),
        ]
    )


class BasePseRceSensor(CoordinatorEntity[PseRceCoordinator], SensorEntity):
    """Base class for PSE RCE sensors providing common DeviceInfo."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "PLN/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: PseRceCoordinator, entry: ConfigEntry) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="PSE RCE Monitor",
            manufacturer="Polskie Sieci Elektroenergetyczne",
            model="RCE-PLN API Service",
            entry_type=DeviceInfo.EntryType.SERVICE if hasattr(DeviceInfo, "EntryType") else None,
        )


class PseRcePriceChainSensor(BasePseRceSensor):
    """Representation of the PSE RCE Price Chain sensor."""

    _attr_translation_key = "pse_rce_price_chain"
    _attr_icon = "mdi:currency-pln"

    def __init__(self, coordinator: PseRceCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_price_chain"

    @property
    def native_value(self) -> float | None:
        """Return the current price."""
        if self.coordinator.data:
            return self.coordinator.data.get("native_value")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return the forecast price chain list."""
        if self.coordinator.data:
            return {
                "list": self.coordinator.data.get("list", []),
                "forecast_start": self.coordinator.data.get("forecast_start"),
                "resolution": self.coordinator.data.get("resolution"),
                "start_from_midnight": self.coordinator.data.get(
                    "start_from_midnight", False
                ),
            }
        return {
            "list": [],
            "forecast_start": None,
            "resolution": None,
            "start_from_midnight": False,
        }


class PseRceTodayMinPriceSensor(BasePseRceSensor):
    """Representation of today's minimum PSE RCE price."""

    _attr_translation_key = "pse_rce_today_min_price"
    _attr_icon = "mdi:arrow-down-bold-circle-outline"

    def __init__(self, coordinator: PseRceCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_today_min_price"

    @property
    def native_value(self) -> float | None:
        """Return today's minimum price."""
        if self.coordinator.data:
            return self.coordinator.data.get("today_min_price")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return the timestamp of the minimum price."""
        if self.coordinator.data:
            return {"dtime": self.coordinator.data.get("today_min_time")}
        return {"dtime": None}


class PseRceTodayMaxPriceSensor(BasePseRceSensor):
    """Representation of today's maximum PSE RCE price."""

    _attr_translation_key = "pse_rce_today_max_price"
    _attr_icon = "mdi:arrow-up-bold-circle-outline"

    def __init__(self, coordinator: PseRceCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_today_max_price"

    @property
    def native_value(self) -> float | None:
        """Return today's maximum price."""
        if self.coordinator.data:
            return self.coordinator.data.get("today_max_price")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return the timestamp of the maximum price."""
        if self.coordinator.data:
            return {"dtime": self.coordinator.data.get("today_max_time")}
        return {"dtime": None}