"""Constants for the PSE RCE integration."""
DOMAIN = "pse_rce"
PSE_API_URL = "https://api.raporty.pse.pl/api/rce-pln"

CONF_HORIZON = "horizon"
DEFAULT_HORIZON = 24

CONF_START_FROM_MIDNIGHT = "start_from_midnight"
DEFAULT_START_FROM_MIDNIGHT = False

CONF_RESOLUTION = "resolution"
DEFAULT_RESOLUTION = "15m"

CONF_FALLBACK_STRATEGY = "fallback_strategy"
DEFAULT_FALLBACK_STRATEGY = "last"

CONF_CLAMP_NEGATIVE = "clamp_negative_prices"
DEFAULT_CLAMP_NEGATIVE = False

CONF_PRICE_FACTOR = "price_factor"
DEFAULT_PRICE_FACTOR = 1.23

CONF_PRICE_OFFSET = "price_offset"
DEFAULT_PRICE_OFFSET = 0.0