"""
cape_service.py
Fetches Shiller CAPE ratio data from FRED API with:
  - 24-hour in-memory cache
  - Graceful fallback to hardcoded recent values if API unavailable
  - International CAPE from hardcoded research data (no free API exists)
"""

import time
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# ── In-memory cache ──────────────────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL = 86400  # 24 hours in seconds

# ── Fallback values (updated manually, last checked 2025-06) ────────────────
# Source: multpl.com / Shiller data
FALLBACK_SP500_CAPE = 32.0

# International CAPE — Source: StarCapital / Research Affiliates / MSCI
# These change slowly (monthly); updating quarterly is sufficient
INTERNATIONAL_CAPE = {
    "msci-world-exus":    17.0,
    "msci-em":            14.0,
    "msci-europe":        16.0,
    "sp500":              32.0,   # overwritten by live FRED if available
    "msci-acwi":          27.0,
    "msci-japan":         19.0,
    "msci-em-exchina":    13.0,
    "msci-world-smallcap":20.0,
    "stoxx600":           15.0,
    "msci-india":         32.0,
}

# Source links for each — shown in the UI so users can verify
CAPE_SOURCES = {
    "sp500":              "https://www.multpl.com/shiller-pe",
    "msci-world-exus":    "https://www.starcapital.de/en/research/stock-market-valuation/",
    "msci-em":            "https://www.starcapital.de/en/research/stock-market-valuation/",
    "msci-europe":        "https://www.starcapital.de/en/research/stock-market-valuation/",
    "msci-acwi":          "https://www.starcapital.de/en/research/stock-market-valuation/",
    "msci-japan":         "https://www.starcapital.de/en/research/stock-market-valuation/",
    "msci-em-exchina":    "https://www.starcapital.de/en/research/stock-market-valuation/",
    "msci-world-smallcap":"https://www.starcapital.de/en/research/stock-market-valuation/",
    "stoxx600":           "https://www.starcapital.de/en/research/stock-market-valuation/",
    "msci-india":         "https://www.starcapital.de/en/research/stock-market-valuation/",
}


def _is_cache_valid(key: str) -> bool:
    if key not in _cache:
        return False
    return (time.time() - _cache[key]["timestamp"]) < CACHE_TTL


async def fetch_sp500_cape_from_fred() -> dict:
    """
    Fetch S&P 500 Shiller CAPE from FRED.
    Series ID: CAPE (Cyclically Adjusted Price Earnings Ratio)
    Returns dict with value, date, source.
    """
    cache_key = "fred_sp500_cape"
    if _is_cache_valid(cache_key):
        return _cache[cache_key]["data"]

    if not FRED_API_KEY or FRED_API_KEY == "your_fred_api_key_here":
        # No API key — return fallback
        result = {
            "value": FALLBACK_SP500_CAPE,
            "date": "hardcoded fallback",
            "source": CAPE_SOURCES["sp500"],
            "live": False,
            "note": "Set FRED_API_KEY in .env to enable live data"
        }
        return result

    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id=CAPE"
        f"&api_key={FRED_API_KEY}"
        f"&file_type=json"
        f"&sort_order=desc"
        f"&limit=1"
    )

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            obs = data["observations"][0]
            value = float(obs["value"])
            date  = obs["date"]

            result = {
                "value":  round(value, 1),
                "date":   date,
                "source": CAPE_SOURCES["sp500"],
                "live":   True,
                "note":   f"Live from FRED · Series: CAPE · As of {date}"
            }
            _cache[cache_key] = {"data": result, "timestamp": time.time()}
            return result

    except Exception as e:
        # FRED unavailable — use fallback silently
        result = {
            "value":  FALLBACK_SP500_CAPE,
            "date":   "fallback",
            "source": CAPE_SOURCES["sp500"],
            "live":   False,
            "note":   f"FRED unavailable ({str(e)[:60]}), using fallback value"
        }
        return result


async def get_all_cape_data() -> dict:
    """
    Returns CAPE data for all indices.
    S&P 500 is live from FRED (with 24h cache).
    All others are hardcoded research values with source links.
    """
    cache_key = "all_cape"
    if _is_cache_valid(cache_key):
        return _cache[cache_key]["data"]

    # Fetch live S&P 500
    sp500_data = await fetch_sp500_cape_from_fred()

    # Build full dataset
    result = {}
    for idx_id, cape_val in INTERNATIONAL_CAPE.items():
        if idx_id == "sp500":
            result[idx_id] = {
                "cape":   sp500_data["value"],
                "source": sp500_data["source"],
                "live":   sp500_data["live"],
                "note":   sp500_data["note"],
                "last_updated": sp500_data.get("date", "unknown")
            }
        else:
            result[idx_id] = {
                "cape":   cape_val,
                "source": CAPE_SOURCES.get(idx_id, ""),
                "live":   False,
                "note":   "Research estimate — update quarterly from StarCapital",
                "last_updated": "2025-Q2"
            }

    result["_meta"] = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "sp500_live": sp500_data["live"],
        "cache_ttl_hours": CACHE_TTL // 3600
    }

    _cache[cache_key] = {"data": result, "timestamp": time.time()}
    return result
