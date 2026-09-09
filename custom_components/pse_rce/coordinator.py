"""Data update coordinator for PSE RCE."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
        self.horizon_hours = int(horizon_hours)
        self.start_from_midnight = start_from_midnight
        self.resolution = resolution
        self.fallback_strategy = fallback_strategy
        self.clamp_negative_prices = clamp_negative_prices
        self.price_factor = float(price_factor)
        self.price_offset = float(price_offset)
        
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
        """Fetch prices perfectly mapped to configuration periods."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        query_url = f"{PSE_API_URL}?$filter=business_date%20ge%20'{today_str}'"
        
        headers = {
            "accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(query_url, headers=headers, timeout=20) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Błąd pobierania z API PSE, status: {response.status}")
                data = await response.json()
                
        records = data.get("value", [])
        if not records:
            raise UpdateFailed(f"API PSE nie zwróciło rekordów od daty {today_str}")

        price_dict = {}
        for record in records:
            dtime_str = record.get("dtime")
            rce_pln = record.get("rce_pln")
            
            if dtime_str and rce_pln is not None:
                try:
                    price_dict[str(dtime_str).strip()] = round(float(rce_pln) / 1000.0, 5)
                except (ValueError, TypeError):
                    continue

        if not price_dict:
            raise UpdateFailed("Brak poprawnych cen RCE do zmapowania w odpowiedzi")

        now = datetime.now()
        step_minutes = 30 if self.resolution == "30m" else 15
        total_steps = self.horizon_hours * (60 // step_minutes)

        if self.start_from_midnight:
            start_dt = now.replace(hour=0, minute=step_minutes, second=0, microsecond=0)
        else:
            minutes_to_add = step_minutes - (now.minute % step_minutes)
            start_dt = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)

        def _get_price_for_timestamp(target_timestamp: datetime) -> float | None:
            """Pobiera pojedynczy punkt cenowy z API z opcjonalnym uśrednianiem 30m."""
            if step_minutes == 30:
                val1_dt = target_timestamp - timedelta(minutes=15)
                val2_dt = target_timestamp
                v1 = price_dict.get(val1_dt.strftime("%Y-%m-%d %H:%M:%S"))
                v2 = price_dict.get(val2_dt.strftime("%Y-%m-%d %H:%M:%S"))
                
                if v1 is not None and v2 is not None:
                    return (v1 + v2) / 2
                if v1 is not None:
                    return v1
                if v2 is not None:
                    return v2
                return None
            return price_dict.get(target_timestamp.strftime("%Y-%m-%d %H:%M:%S"))

        result: list[float] = []

        for i in range(total_steps):
            target_dt = start_dt + timedelta(minutes=step_minutes * i)
            val = _get_price_for_timestamp(target_dt)
            
            if val is not None:
                result.append(self._transform_price(val))
            else:
                if self.fallback_strategy == "repeat":
                    past_val = None
                    days_back = 1
                    while past_val is None and days_back <= 7:
                        lookup_dt = target_dt - timedelta(days=days_back)
                        past_val = _get_price_for_timestamp(lookup_dt)
                        days_back += 1
                    
                    if past_val is not None:
                        result.append(self._transform_price(past_val))
                    else:
                        fallback_val = result[-1] if result else self._transform_price(list(price_dict.values())[0])
                        result.append(fallback_val)

                elif self.fallback_strategy == "zero":
                    result.append(0.0)

                else:  # "last"
                    fallback_val = result[-1] if result else self._transform_price(list(price_dict.values())[0])
                    result.append(fallback_val)

        current_price = result[0] if result else 0.0

        # Bezpieczne obliczanie min i max dla bieżącej doby
        today_min_price = None
        today_min_time = None
        today_max_price = None
        today_max_time = None

        try:
            today_prefix = today_str  # "YYYY-MM-DD"
            tomorrow_prefix = (now.date() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            today_prices = []
            for dtime_k, raw_val in price_dict.items():
                # Rekordy z dzisiaj lub dokładnie północ zamykająca dobę (np. YYYY-MM-DD 00:00:00 dnia jutrzejszego)
                if dtime_k.startswith(today_prefix):
                    today_prices.append((self._transform_price(raw_val), dtime_k))
                elif dtime_k.startswith(f"{tomorrow_prefix} 00:00:00"):
                    today_prices.append((self._transform_price(raw_val), dtime_k))

            if today_prices:
                min_item = min(today_prices, key=lambda x: x[0])
                max_item = max(today_prices, key=lambda x: x[0])
                today_min_price = min_item[0]
                today_min_time = min_item[1]
                today_max_price = max_item[0]
                today_max_time = max_item[1]
        except Exception as err:
            _LOGGER.warning("Nie udało się wyznaczyć min/max dla doby: %s", err)

        return {
            "native_value": current_price,
            "list": result[:total_steps],
            "today_min_price": today_min_price,
            "today_min_time": today_min_time,
            "today_max_price": today_max_price,
            "today_max_time": today_max_time,
        }