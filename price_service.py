"""
price_service.py
Fetches historical price data for index ETF proxies via yfinance.
24-hour in-memory cache per ticker per period.
No pandas dependency — data extracted from DataFrame using .tolist() only.
"""

import time
import traceback
from datetime import datetime

# ── Cache ────────────────────────────────────────────────────────────────────
_price_cache: dict = {}
CACHE_TTL = 86400  # 24 hours

# ── Index → ETF proxy ────────────────────────────────────────────────────────
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


def _fetch_ticker(ticker: str, period: str, interval: str) -> tuple[list[dict], str | None]:
    """
    Fetch OHLC from Yahoo Finance.
    Returns (data_list, error_message).
    error_message is None on success.
    Uses only .tolist() on DataFrame columns — no pandas methods.
    """
    try:
        import yfinance as yf
    except ImportError as e:
        return [], f"yfinance not installed: {e}"

    try:
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period=period, interval=interval, auto_adjust=True)
    except Exception as e:
        return [], f"yfinance.history() failed for {ticker}: {traceback.format_exc()}"

    try:
        if df is None or len(df) == 0:
            return [], f"Empty dataframe returned for {ticker} period={period}"

        # Extract as plain Python lists — avoids any pandas version issues
        dates  = df.index.tolist()
        closes = df["Close"].tolist()
        opens  = df["Open"].tolist()
        highs  = df["High"].tolist()
        lows   = df["Low"].tolist()

        result = []
        for i, d in enumerate(dates):
            # Timestamps stringify to "2024-01-15 00:00:00+00:00" — take first 10 chars
            date_str = str(d)[:10]
            close_val = closes[i]
            if close_val is None or (hasattr(close_val, '__class__') and close_val.__class__.__name__ == 'float' and close_val != close_val):
                continue  # skip NaN rows
            result.append({
                "date":  date_str,
                "close": round(float(close_val), 2),
                "open":  round(float(opens[i] or close_val), 2),
                "high":  round(float(highs[i] or close_val), 2),
                "low":   round(float(lows[i]  or close_val), 2),
            })

        if not result:
            return [], f"All rows were NaN for {ticker}"

        return result, None

    except Exception as e:
        return [], f"Data extraction failed for {ticker}: {traceback.format_exc()}"


def get_index_prices(index_id: str, period: str = "1Y") -> dict:
    """
    Returns price history for one index with full error detail.
    On failure returns {"error": "...", "detail": "..."} for debugging.
    """
    if index_id not in INDEX_TICKERS:
        return {"error": f"Unknown index: {index_id}"}

    meta   = INDEX_TICKERS[index_id]
    ticker = meta["ticker"]
    pcfg   = PERIODS.get(period, PERIODS["1Y"])
    key    = _cache_key(ticker, period)

    if _is_valid(key):
        return {**_price_cache[key]["data"], "cached": True}

    print(f"[price] Fetching {ticker} period={period} interval={pcfg['interval']}")
    raw, err = _fetch_ticker(ticker, pcfg["period"], pcfg["interval"])

    if err or not raw:
        print(f"[price] FAILED {ticker}: {err}")
        return {
            "error":    f"Could not load price data for {ticker}",
            "detail":   err or "Empty result",
            "index_id": index_id,
            "ticker":   ticker,
        }

    first_close = raw[0]["close"]
    last_close  = raw[-1]["close"]
    period_high = max(r["close"] for r in raw)
    perf_pct    = round((last_close - first_close) / first_close * 100, 2)
    from_high   = round((last_close - period_high) / period_high * 100, 2)

    print(f"[price] OK {ticker}: {len(raw)} rows, latest={last_close}, perf={perf_pct}%")

    result = {
        "index_id":      index_id,
        "name":          meta["name"],
        "ticker":        ticker,
        "currency":      meta["currency"],
        "period":        period,
        "data":          raw,
        "current":       last_close,
        "perf_pct":      perf_pct,
        "from_high_pct": from_high,
        "period_high":   period_high,
        "fetched_at":    datetime.utcnow().isoformat() + "Z",
        "cached":        False,
    }

    _price_cache[key] = {"data": result, "ts": time.time()}
    return result


def get_all_prices(period: str = "1Y") -> dict:
    results = {}
    for idx_id in INDEX_TICKERS:
        results[idx_id] = get_index_prices(idx_id, period)
    return results


def get_comparison_data(index_ids: list[str], period: str = "1Y") -> dict:
    series = {}
    for idx_id in index_ids:
        data = get_index_prices(idx_id, period)
        if "error" not in data and data.get("data"):
            first = data["data"][0]["close"]
            series[idx_id] = {
                "name":     data["name"],
                "ticker":   data["ticker"],
                "points":   [
                    {"date": d["date"], "value": round(d["close"] / first * 100, 2)}
                    for d in data["data"]
                ],
                "perf_pct": data["perf_pct"],
            }
    return series
