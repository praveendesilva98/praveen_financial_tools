# Praveen's Financial Tools

A personal finance website with two tools:
- **APEX Simulator** — Block bootstrap portfolio simulator with CAPE-adjusted drift
- **Index Recommender** — Systematic 5-factor index scoring with live CAPE from FRED

## Stack

- **Backend**: Python 3.11+ / FastAPI / Uvicorn
- **Templates**: Jinja2
- **Frontend**: Vanilla JS + Chart.js (CDN)
- **Data**: FRED API (live S&P 500 CAPE) + embedded historical data

---

## Setup

### 1. Clone / download the project

```bash
cd praveen-financial
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your FRED API key.
Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html
(Takes 30 seconds, completely free)

Without a FRED key the S&P 500 CAPE falls back to a hardcoded estimate.
Everything else still works.

### 5. Run locally

```bash
python main.py
```

Open http://localhost:8000 in your browser.

---

## Project structure

```
praveen-financial/
├── main.py               # FastAPI app — routes and startup
├── cape_service.py       # FRED API fetch + 24h cache + fallback data
├── requirements.txt
├── .env.example          # Copy to .env and fill in FRED_API_KEY
├── static/
│   ├── style.css         # Shared design system (dark terminal theme)
│   └── app.js            # Shared JS utilities (fmtM, pctile, gauss, etc.)
└── templates/
    ├── base.html         # Navbar + footer shell
    ├── index.html        # Landing page
    ├── apex.html         # APEX Portfolio Simulator
    ├── recommender.html  # Index Recommender
    └── about.html        # Methodology page
```

---

## Deployment (free options)

### GitHub Pages
Not suitable — requires a Python backend. Use one of the options below.

### Railway (recommended — free tier)
1. Push code to a GitHub repository
2. Go to railway.app → New Project → Deploy from GitHub
3. Set environment variable `FRED_API_KEY` in Railway dashboard
4. Railway auto-detects Python and runs `uvicorn main:app`
5. Custom domain available on free tier

### Render
1. Push to GitHub
2. render.com → New Web Service → connect repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add `FRED_API_KEY` in environment variables
6. Free tier spins down after 15 min inactivity (cold start ~30s)

### Fly.io
More control, always-on free tier, requires `flyctl` CLI.
```bash
fly launch
fly secrets set FRED_API_KEY=your_key_here
fly deploy
```

---

## Updating CAPE data

**S&P 500 CAPE** — automatic via FRED API, cached 24 hours.

**International CAPE** — update quarterly in `cape_service.py`:
```python
INTERNATIONAL_CAPE = {
    "msci-world-exus":    17.0,   # ← update these
    "msci-em":            14.0,
    ...
}
```

Sources to check:
- StarCapital: https://www.starcapital.de/en/research/stock-market-valuation/
- Research Affiliates: https://www.researchaffiliates.com/asset-allocation

---

## API endpoints

| Endpoint        | Description                              |
|-----------------|------------------------------------------|
| `GET /`         | Landing page                             |
| `GET /apex`     | APEX Simulator                           |
| `GET /recommender` | Index Recommender                     |
| `GET /about`    | Methodology                              |
| `GET /api/cape` | JSON: all CAPE data (live + estimates)   |
| `GET /api/health` | Health check                           |

---

## Adding new indices

In `cape_service.py`, add to `INTERNATIONAL_CAPE` and `CAPE_SOURCES`.
In `recommender.html`, add an entry to the `INDICES` array with all fields.

---

## License
Personal use. Not financial advice.
