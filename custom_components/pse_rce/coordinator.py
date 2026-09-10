"""Data update coordinator for PSE RCE."""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
import logging
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import PSE_API_URL

_LOGGER = logging.getLogger(__name__)

class PseRceCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch and format RCE price chains from PSE API."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        horizon_hours: int, 
        start_from_midnight: bool, 
        resolution: str, 
        fallback_strategy: str,
        clamp_negative_prices: bool,
        price_factor: float,
        price_offset: float,
    ) -> None:
        """Initialize coordinator."""
        self.horizon_hours = min(max(int(horizon_hours), 1), 48)
        self.start_from_midnight = start_from_midnight
        self.resolution = resolution
        self.fallback_strategy = fallback_strategy
        self.clamp_negative_prices = clamp_negative_prices
        self.price_factor = float(price_factor)
        self.price_offset = float(price_offset)
        
        if resolution not in ("15m", "30m"):
            raise ValueError(f"Unsupported PSE RCE resolution: {resolution}")

        update_interval = timedelta(minutes=30) if resolution == "30m" else timedelta(minutes=15)
        
        super().__init__(
            hass,
            _LOGGER,
            name="PSE RCE Coordinator",
            update_interval=update_interval,
        )

    def _transform_price(self, price: float) -> float:
        """Apply price factor, offset and clamp negative values if enabled."""
        adjusted = (price * self.price_factor) + self.price_offset
        if self.clamp_negative_prices and adjusted < 0.0:
            adjusted = 0.0
        return round(adjusted, 5)

    async def _async_update_data(self) -> dict:
        """Fetch prices for the surrounding business dates and build a time chain."""
        now = dt_util.now().replace(second=0, microsecond=0, tzinfo=None)
        today = now.date()
        target_dates = [today - timedelta(days=1), today, today + timedelta(days=1)]
        headers = {
            "accept": "application/json",
            "User-Agent": "Home Assistant PSE RCE integration",
        }

        records: list[dict] = []
        async with aiohttp.ClientSession() as session:
            for target_date in target_dates:
                date_string = target_date.isoformat()
                query_url = f"{PSE_API_URL}?$filter=business_date%20eq%20'{date_string}'"
                try:
                    async with session.get(query_url, headers=headers, timeout=20) as response:
                        if response.status != 200:
                            _LOGGER.warning(
                                "Błąd pobierania z API PSE (%s), status: %s",
                                date_string,
                                response.status,
                            )
                            continue
                        data = await response.json()
                except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
                    _LOGGER.warning("Nie udało się pobrać danych PSE dla %s: %s", date_string, err)
                    continue
                records.extend(data.get("value", []))

        price_dict: dict[datetime, float] = {}
        business_dates: dict[datetime, date] = {}
        for record in records:
            dtime_value = record.get("dtime")
            rce_pln = record.get("rce_pln")
            business_date = record.get("business_date")
            if not dtime_value or rce_pln is None or not business_date:
                continue
            try:
                dtime = datetime.fromisoformat(
                    str(dtime_value).strip().replace("Z", "+00:00")
                )
                if dtime.tzinfo is not None:
                    dtime = dt_util.as_local(dtime).replace(tzinfo=None)
                price_dict[dtime] = round(float(rce_pln) / 1000.0, 5)
                business_dates[dtime] = date.fromisoformat(str(business_date))
            except (ValueError, TypeError):
                continue

        if not price_dict:
            raise UpdateFailed("Brak poprawnych cen RCE do zmapowania w odpowiedzi")

        step_minutes = 30 if self.resolution == "30m" else 15
        total_steps = self.horizon_hours * (60 // step_minutes)
        if self.start_from_midnight:
            start_dt = now.replace(hour=0, minute=step_minutes, second=0, microsecond=0)
        else:
            minutes_to_add = (-now.minute) % step_minutes or step_minutes
            start_dt = now + timedelta(minutes=minutes_to_add)

        def get_price(target_timestamp: datetime) -> float | None:
            """Read one end-of-period value, averaging two quarters for 30m."""
            if step_minutes == 30:
                values = [
                    price_dict.get(target_timestamp - timedelta(minutes=15)),
                    price_dict.get(target_timestamp),
                ]
                values = [value for value in values if value is not None]
                return sum(values) / len(values) if values else None
            return price_dict.get(target_timestamp)

        first_raw_value = next(iter(price_dict.values()))
        result: list[float] = []
        for index in range(total_steps):
            target_dt = start_dt + timedelta(minutes=step_minutes * index)
            raw_value = get_price(target_dt)
            if raw_value is None and self.fallback_strategy == "repeat":
                for days_back in range(1, 8):
                    raw_value = get_price(target_dt - timedelta(days=days_back))
                    if raw_value is not None:
                        break
            if raw_value is None:
                if self.fallback_strategy == "zero":
                    result.append(0.0)
                elif result:
                    result.append(result[-1])
                else:
                    result.append(self._transform_price(first_raw_value))
            else:
                result.append(self._transform_price(raw_value))

        today_prices = [
            (self._transform_price(raw_value), timestamp)
            for timestamp, raw_value in price_dict.items()
            if business_dates.get(timestamp) == today
        ]
        today_min_price = today_min_time = today_max_price = today_max_time = None
        if today_prices:
            min_item = min(today_prices, key=lambda item: item[0])
            max_item = max(today_prices, key=lambda item: item[0])
            today_min_price, today_min_time = min_item[0], min_item[1].isoformat(sep=" ")
            today_max_price, today_max_time = max_item[0], max_item[1].isoformat(sep=" ")

        return {
            "native_value": result[0] if result else 0.0,
            "list": result,
            "forecast_start": start_dt.isoformat(),
            "resolution": self.resolution,
            "start_from_midnight": self.start_from_midnight,
            "today_min_price": today_min_price,
            "today_min_time": today_min_time,
            "today_max_price": today_max_price,
            "today_max_time": today_max_time,
        }