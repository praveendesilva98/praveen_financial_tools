"""
main.py — Praveen's Financial Tools
FastAPI backend serving the portfolio simulator and index recommender.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import uvicorn

from cape_service import get_all_cape_data

# ── App lifecycle ────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm CAPE cache on startup
    try:
        await get_all_cape_data()
        print("✓ CAPE data cache warmed")
    except Exception as e:
        print(f"⚠ CAPE pre-warm failed: {e}")
    yield

app = FastAPI(
    title="Praveen's Financial Tools",
    description="Portfolio simulator and index recommender",
    version="1.0.0",
    lifespan=lifespan
)

# ── Static files & templates ─────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ════════════════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/apex", response_class=HTMLResponse)
async def apex(request: Request):
    """APEX Portfolio Simulator page"""
    cape_data = await get_all_cape_data()
    sp500_cape = cape_data.get("sp500", {}).get("cape", 32.0)
    sp500_live  = cape_data.get("sp500", {}).get("live", False)
    sp500_note  = cape_data.get("sp500", {}).get("note", "")
    return templates.TemplateResponse("apex.html", {
        "request":    request,
        "sp500_cape": sp500_cape,
        "sp500_live": sp500_live,
        "sp500_note": sp500_note,
    })


@app.get("/recommender", response_class=HTMLResponse)
async def recommender(request: Request):
    """Index Recommender page"""
    cape_data = await get_all_cape_data()
    meta = cape_data.pop("_meta", {})
    return templates.TemplateResponse("recommender.html", {
        "request":   request,
        "cape_data": cape_data,
        "meta":      meta,
    })


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


# ════════════════════════════════════════════════════════════════════════
#  API ROUTES
# ════════════════════════════════════════════════════════════════════════

@app.get("/api/cape")
async def api_cape():
    """
    Returns current CAPE data for all tracked indices.
    S&P 500 is live from FRED (24h cached).
    International indices are research estimates.
    """
    data = await get_all_cape_data()
    return data


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Praveen's Financial Tools"}


# ── Dev server entry point ───────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
