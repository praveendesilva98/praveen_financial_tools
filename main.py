"""
main.py — Praveen's Financial Tools
FastAPI backend: portfolio simulator + index recommender + live price charts.
"""

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import uvicorn

from cape_service import get_all_cape_data
from price_service import get_index_prices, get_all_prices, get_comparison_data, INDEX_TICKERS

# ── Lifespan: pre-warm caches on startup ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await get_all_cape_data()
        print("✓ CAPE cache warmed")
    except Exception as e:
        print(f"⚠ CAPE pre-warm failed: {e}")
    yield

app = FastAPI(
    title="Praveen's Financial Tools",
    version="1.0.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "active": "home"})


@app.get("/apex", response_class=HTMLResponse)
async def apex(request: Request):
    cape_data  = await get_all_cape_data()
    sp500      = cape_data.get("sp500", {})
    return templates.TemplateResponse("apex.html", {
        "request":    request,
        "active":     "apex",
        "sp500_cape": sp500.get("cape", 32.0),
        "sp500_live": sp500.get("live", False),
        "sp500_note": sp500.get("note", ""),
    })


@app.get("/recommender", response_class=HTMLResponse)
async def recommender(request: Request):
    cape_data = await get_all_cape_data()
    meta      = cape_data.pop("_meta", {})
    # Pass available tickers list to template for chart init
    tickers   = {k: v["ticker"] for k, v in INDEX_TICKERS.items()}
    return templates.TemplateResponse("recommender.html", {
        "request":   request,
        "active":    "recommender",
        "cape_data": cape_data,
        "meta":      meta,
        "tickers":   tickers,
    })


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "active": "about"})


# ════════════════════════════════════════════════════════════
#  API ROUTES
# ════════════════════════════════════════════════════════════

@app.get("/api/cape")
async def api_cape():
    """Current CAPE data for all tracked indices."""
    return await get_all_cape_data()


@app.get("/api/prices/{index_id}")
def api_prices_single(
    index_id: str,
    period: str = Query(default="1Y", regex="^(1Y|3Y|5Y|10Y)$")
):
    """Price history for one index. period = 1Y | 3Y | 5Y | 10Y"""
    return get_index_prices(index_id, period)


@app.get("/api/prices")
def api_prices_all(
    period: str = Query(default="1Y", regex="^(1Y|3Y|5Y|10Y)$")
):
    """Price history for all tracked indices."""
    return get_all_prices(period)


@app.get("/api/comparison")
def api_comparison(
    ids:    str    = Query(default="sp500,msci-world-exus,msci-em,stoxx600"),
    period: str    = Query(default="1Y", regex="^(1Y|3Y|5Y|10Y)$")
):
    """
    Normalised (base=100) comparison data for multiple indices.
    ids = comma-separated index IDs.
    """
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    return get_comparison_data(id_list, period)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Praveen's Financial Tools"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
