"""
price_service.py
Fetches historical price data for index ETF proxies via yfinance.
24-hour cache per ticker per period to avoid hammering Yahoo.
"""

import time
import yfinance as yf
from datetime import datetime, timedelta

# ── Cache ────────────────────────────────────────────────────────────────────
_price_cache: dict = {}
CACHE_TTL = 86400  # 24 hours — daily data, no point refreshing more often

# ── Index → ETF proxy mapping ────────────────────────────────────────────────
# Using the most liquid, widely-available ETFs as proxies for each index.
# All listed on major exchanges, data available via Yahoo Finance.
INDEX_TICKERS = {
    "sp500":               {"ticker": "SPY",  "name": "S&P 500",              "currency": "USD"},
    "msci-world-exus":     {"ticker": "EFA",  "name": "MSCI World ex-USA",    "currency": "USD"},
    "msci-em":             {"ticker": "EEM",  "name": "MSCI Emerging Markets","currency": "USD"},
    "msci-europe":         {"ticker": "VGK",  "name": "MSCI Europe",          "currency": "USD"},
    "msci-acwi":           {"ticker": "ACWI", "name": "MSCI ACWI",            "currency": "USD"},
    "msci-japan":          {"ticker": "EWJ",  "name": "MSCI Japan",           "currency": "USD"},
    "msci-em-exchina":     {"ticker": "EMXC", "name": "MSCI EM ex-China",     "currency": "USD"},
    "msci-world-smallcap": {"ticker": "VSS",  "name": "MSCI World Small Cap", "currency": "USD"},
    "stoxx600":            {"ticker": "FEZ",  "name": "STOXX Europe 600",     "currency": "USD"},
    "msci-india":          {"ticker": "INDA", "name": "MSCI India",           "currency": "USD"},
}

# Period configs
PERIODS = {
    "1Y":  {"period": "1y",  "interval": "1wk"},
    "3Y":  {"period": "3y",  "interval": "1wk"},
    "5Y":  {"period": "5y",  "interval": "1mo"},
    "10Y": {"period": "10y", "interval": "1mo"},
}


def _cache_key(ticker: str, period: str) -> str:
    return f"{ticker}_{period}"


def _is_valid(key: str) -> bool:
    if key not in _price_cache:
        return False
    return (time.time() - _price_cache[key]["ts"]) < CACHE_TTL


def _fetch_ticker(ticker: str, period: str, interval: str) -> list[dict]:
    """Fetch OHLC data from Yahoo Finance. Returns list of {date, close, open, high, low}."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return []
        df = df.reset_index()
        # Date column can be 'Date' or 'Datetime'
        date_col = "Date" if "Date" in df.columns else "Datetime"
        result = []
        for _, row in df.iterrows():
            d = row[date_col]
            date_str = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10]
            result.append({
                "date":  date_str,
                "close": round(float(row["Close"]), 2),
                "open":  round(float(row["Open"]),  2),
                "high":  round(float(row["High"]),  2),
                "low":   round(float(row["Low"]),   2),
            })
        return result
    except Exception as e:
        print(f"yfinance error for {ticker} ({period}): {e}")
        return []


def get_index_prices(index_id: str, period: str = "1Y") -> dict:
    """
    Returns price history for one index.
    {
      "index_id": ...,
      "name": ...,
      "ticker": ...,
      "period": ...,
      "data": [{date, close, open, high, low}, ...],
      "perf_pct": float,       # % change over period
      "current": float,        # latest close
      "from_high_pct": float,  # % drawdown from period high
      "cached": bool
    }
    """
    if index_id not in INDEX_TICKERS:
        return {"error": f"Unknown index: {index_id}"}

    meta   = INDEX_TICKERS[index_id]
    ticker = meta["ticker"]
    pcfg   = PERIODS.get(period, PERIODS["1Y"])
    key    = _cache_key(ticker, period)

    if _is_valid(key):
        return {**_price_cache[key]["data"], "cached": True}

    raw = _fetch_ticker(ticker, pcfg["period"], pcfg["interval"])

    if not raw:
        return {"error": f"No data for {ticker}", "index_id": index_id}

    first_close = raw[0]["close"]
    last_close  = raw[-1]["close"]
    period_high = max(r["close"] for r in raw)
    perf_pct    = round((last_close - first_close) / first_close * 100, 2)
    from_high   = round((last_close - period_high) / period_high * 100, 2)

    result = {
        "index_id":     index_id,
        "name":         meta["name"],
        "ticker":       ticker,
        "currency":     meta["currency"],
        "period":       period,
        "data":         raw,
        "current":      last_close,
        "perf_pct":     perf_pct,
        "from_high_pct":from_high,
        "period_high":  period_high,
        "fetched_at":   datetime.utcnow().isoformat() + "Z",
        "cached":       False,
    }

    _price_cache[key] = {"data": result, "ts": time.time()}
    return result


def get_all_prices(period: str = "1Y") -> dict:
    """Fetch prices for all tracked indices. Returns dict keyed by index_id."""
    results = {}
    for idx_id in INDEX_TICKERS:
        results[idx_id] = get_index_prices(idx_id, period)
    return results


def get_comparison_data(index_ids: list[str], period: str = "1Y") -> dict:
    """
    Returns normalised (base 100) price series for multiple indices,
    aligned to the same date range for comparison charting.
    """
    series = {}
    for idx_id in index_ids:
        data = get_index_prices(idx_id, period)
        if "error" not in data and data.get("data"):
            first = data["data"][0]["close"]
            series[idx_id] = {
                "name":   data["name"],
                "ticker": data["ticker"],
                "points": [
                    {"date": d["date"], "value": round(d["close"] / first * 100, 2)}
                    for d in data["data"]
                ],
                "perf_pct": data["perf_pct"],
            }
    return series
