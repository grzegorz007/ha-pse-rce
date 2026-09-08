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

    def __init__(self, hass: HomeAssistant, horizon: int, start_from_midnight: bool) -> None:
        """Initialize coordinator."""
        self.horizon = horizon
        self.start_from_midnight = start_from_midnight
        super().__init__(
            hass,
            _LOGGER,
            name="PSE RCE Coordinator",
            update_interval=timedelta(minutes=30),
        )

    async def _async_update_data(self) -> dict:
        """Fetch raw prices from PSE API and align to timeline with 24h rollover fallback."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PSE_API_URL, timeout=15) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Błąd pobierania z API PSE, status: {response.status}")
                    
                    data = await response.json()
                    records = data.get("result", [])

            # 1. Budujemy słownik timestamp -> wartość (PLN/kWh)
            price_dict = {}
            for record in records:
                time_str = record.get("dtime")
                rce_mwh = record.get("rce_pln")
                
                if time_str and rce_mwh is not None:
                    try:
                        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                        if dt.tzinfo is not None:
                            dt = dt.astimezone().replace(tzinfo=None)
                        ts = int(dt.timestamp())
                        price_dict[ts] = float(rce_mwh) / 1000.0  # MWh -> kWh
                    except (ValueError, TypeError):
                        continue

            # 2. Wyznaczamy początek horyzontu
            now = datetime.now()
            if self.start_from_midnight:
                start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                minute = 0 if now.minute < 30 else 30
                start_dt = now.replace(minute=minute, second=0, microsecond=0)
                
            start_ts = int(start_dt.timestamp())

            # 3. Generujemy siatkę co 30 minut z inteligentnym fallbackiem 24h (wstecz o 48 slotów)
            result = []
            for i in range(self.horizon):
                slot_ts = start_ts + (i * 1800)
                val = price_dict.get(slot_ts)
                
                if val is not None:
                    result.append(val)
                else:
                    # Patent: brak cen na jutro -> kopiujemy profil z 24h wcześniej (i - 48)
                    fallback_index = i - 48
                    if 0 <= fallback_index < len(result):
                        result.append(result[fallback_index])
                    elif result:
                        result.append(result[-1])
                    else:
                        result.append(0.0)

            current_price = result[0] if result else 0.0

            return {
                "native_value": current_price,
                "list": result,
            }

        except Exception as err:
            raise UpdateFailed(f"Błąd podczas przetwarzania danych RCE z PSE: {err}") from err