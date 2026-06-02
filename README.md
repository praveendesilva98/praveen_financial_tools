# Praveen's Financial Tools

A personal finance web application built for long-term investors who want honest, valuation-driven tools rather than the optimistic assumptions most retail platforms default to.

Built with **Python / FastAPI** backend, **Jinja2** templates, and **vanilla JavaScript + Chart.js** frontend. Deployable for free on Railway with zero infrastructure to manage.

---

## What it does

### APEX Portfolio Simulator
A portfolio projection engine that runs 10,000 simulated paths using **block bootstrap resampling** of real S&P 500 historical returns (1928–2024), adjusted for current market valuations via the **Shiller CAPE ratio**.

Unlike standard Monte Carlo simulators that assume normally distributed returns, APEX:
- Resamples consecutive blocks of actual historical returns, preserving crash sequences and volatility clustering
- Adjusts the return distribution based on current CAPE — at CAPE 32, expected returns are lower than the long-run average, not equal to it
- Preserves fat tails: the 1931 −43% crash, 2008 −38%, and 2002 −22% all remain in the resampled pool
- Solves the inverse problem: given a target, what annual contribution is required (binary search on the full simulation, not an approximation formula)

**Three panels:** Projections (fan chart, histogram, P10/P25/P50/P75/P90 percentiles) · Target probability (probability of hitting a value, year by year) · Required contribution (how much to invest annually to reach a goal)

### Index Recommender
Systematic scoring of 10 major global indices across 5 weighted dimensions:

| Dimension | Weight | What it measures |
|---|---|---|
| Valuation | 30% | CAPE-implied 10-year forward real return |
| Volatility fit | 20% | Match between index volatility and your horizon + drawdown tolerance |
| Diversification | 20% | Correlation penalty vs existing holdings |
| Tax wrapper fit | 15% | PEA / Assurance Vie / CTO / ISA compatibility |
| Factor quality | 15% | Value, size, quality, reform tilts vs current conditions |

Every score is visible. No black boxes.

**CAPE data for S&P 500 is live from the FRED API** (Federal Reserve Economic Database), cached 24 hours. International CAPE values are research estimates updated quarterly.

**Three tabs:** Recommendation (scored cards with breakdown) · Live Charts (real-time ETF price history via Yahoo Finance, 1Y/3Y/5Y/10Y) · Compare Indices (normalised base-100 comparison of any combination)

---

## Indices covered

| Index | ETF Proxy | CAPE (approx) | Notes |
|---|---|---|---|
| S&P 500 | SPY | ~32 (live) | Elevated — live from FRED |
| MSCI World ex-USA | EFA | ~17 | Fair value |
| MSCI Emerging Markets | EEM | ~14 | Historically cheap |
| MSCI Europe | VGK | ~16 | Fair value |
| MSCI ACWI | ACWI | ~27 | 65% US weighted |
| MSCI Japan | EWJ | ~19 | Governance reform catalyst |
| MSCI EM ex-China | EMXC | ~13 | EM without China risk |
| MSCI World Small Cap | VSS | ~20 | Size premium exposure |
| STOXX Europe 600 | FEZ | ~15 | Broader European coverage |
| MSCI India | INDA | ~32 | Growth story, elevated valuation |

---

## Tech stack

```
Backend     FastAPI + Uvicorn (Python 3.11+)
Templates   Jinja2
Frontend    Vanilla JS + Chart.js (CDN, no build step)
Data        FRED API (live CAPE) · yfinance (price history) · embedded historical returns
Deployment  Railway (free tier)
```

No database. No authentication. No build pipeline. The entire application is a Python process serving HTML templates with JavaScript that runs in the browser.

---

## Project structure

```
praveen-financial/
├── main.py                  # FastAPI app — all routes
├── cape_service.py          # FRED API fetch + 24h cache + fallback values
├── price_service.py         # yfinance price history + normalised comparison
├── requirements.txt
├── .env.example             # Copy to .env — add FRED_API_KEY
│
├── static/
│   ├── style.css            # Full design system — dark terminal theme, mobile-first
│   └── app.js               # Shared utilities (fmtM, pctile, gauss, chart helpers)
│
└── templates/
    ├── base.html            # Navbar + footer shell, mobile hamburger menu
    ├── index.html           # Landing page
    ├── apex.html            # APEX Simulator — all simulation logic in-page JS
    ├── recommender.html     # Index Recommender — scoring + live charts
    └── about.html           # Methodology and data sources
```

---

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Landing page |
| GET | `/apex` | APEX Simulator |
| GET | `/recommender` | Index Recommender |
| GET | `/about` | Methodology |
| GET | `/api/cape` | All CAPE data (S&P 500 live, others estimated) |
| GET | `/api/prices/{index_id}` | Price history for one index · `?period=1Y\|3Y\|5Y\|10Y` |
| GET | `/api/prices` | Price history for all indices |
| GET | `/api/comparison` | Normalised base-100 comparison · `?ids=sp500,msci-em&period=1Y` |
| GET | `/api/health` | Health check |

---

## Local setup

**Requirements:** Python 3.11+

```bash
# 1. Clone the repo
git clone https://github.com/YOURUSERNAME/praveen-financial.git
cd praveen-financial

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — add your FRED API key (see below)

# 5. Run
python main.py
# Open http://localhost:8000
```

The app runs without a FRED key — S&P 500 CAPE falls back to a hardcoded estimate (~32). Everything else works normally.

---

## FRED API key

The FRED API key enables live S&P 500 CAPE data fetched directly from the Federal Reserve.

1. Go to [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
2. Click **Request API Key** — takes 30 seconds, completely free
3. Add to `.env`:
```
FRED_API_KEY=your_key_here
```

The key fetches FRED series `CAPE` (Shiller Cyclically Adjusted PE Ratio). Data is cached in memory for 24 hours — the live badge on each page shows whether the current value is a fresh FRED fetch or a cached/fallback value.

---

## Deploy to Railway (free)

Railway provides free hosting with $5/month credit — more than enough for a personal site.

```bash
# Push to GitHub first
git init && git add . && git commit -m "Initial commit"
git remote add origin https://github.com/YOURUSERNAME/praveen-financial.git
git push -u origin main
```

Then on [railway.app](https://railway.app):

1. **New Project → Deploy from GitHub repo** → select `praveen-financial`
2. Go to **Settings → Start Command** and enter:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
3. Go to **Variables** and add `FRED_API_KEY` with your key
4. Go to **Settings → Networking → Generate Domain** to get your public URL

Railway redeploys automatically on every `git push`. HTTPS is handled automatically.

**Optional custom domain:** buy a `.com` at Namecheap (~€10/year), add it in Railway → Settings → Custom Domain, then add the CNAME record Railway gives you to your domain's DNS. Done.

---

## Updating CAPE data

**S&P 500** — automatic via FRED API. No action needed.

**International indices** — update quarterly in `cape_service.py`:

```python
INTERNATIONAL_CAPE = {
    "msci-world-exus":    17.0,   # update these
    "msci-em":            14.0,
    "msci-europe":        16.0,
    ...
}
```

Reference sources:
- [StarCapital — Global CAPE by country](https://www.starcapital.de/en/research/stock-market-valuation/)
- [Research Affiliates — Asset Allocation](https://www.researchaffiliates.com/asset-allocation)
- [Barclays / MSCI valuation reports](https://www.msci.com/research-and-insights)

---

## Algorithm notes

### Block Bootstrap (APEX)

Each simulated path draws consecutive **blocks** of real historical annual returns with replacement (Politis-Romano stationary bootstrap, 1994). Default block size is 4 years — long enough to preserve bear market / recovery sequences, short enough to maintain combinatorial diversity across the 97-year dataset.

The distribution is then drift-corrected by the ratio of CAPE-implied return to historical mean return:

```
adj_return = (1 + historical_return) × (1 + cape_implied_return) / (1 + hist_mean) - 1
```

This shifts the distribution centre toward current valuations while preserving the shape — fat tails, skewness, and clustering all remain intact.

### CAPE → Forward Return (Recommender)

Forward real return is interpolated from an empirical lookup table calibrated to Campbell & Shiller (1988) and Asness (2012) research:

| CAPE | Implied 10yr Real Return |
|---|---|
| 10 | ~13.8% |
| 15 | ~10.8% |
| 20 | ~7.3% |
| 25 | ~5.8% |
| 30 | ~4.2% |
| 35 | ~2.5% |
| 40 | ~1.2% |
| 45 | ~0.2% |

Higher CAPE → lower expected return. Not a guarantee — a directional signal with ~40% explanatory power over 10-year horizons.

---

## Limitations

This tool is built for honest planning, which means being explicit about what it cannot do:

- **CAPE predicts, not times.** High CAPE means low expected 10-year returns. It says nothing about when any correction happens. The market was expensive in 1996 and doubled before correcting in 2000.
- **US survivorship bias.** The historical dataset is S&P 500 (1928–2024). The US is the market that survived and dominated the 20th century. Bootstrapping from this data embeds that bias. International diversification is partly a hedge against it.
- **yfinance is unofficial.** Yahoo Finance does not provide an official API. The price data endpoint can break or be rate-limited without notice. The 24-hour cache reduces exposure but does not eliminate it.
- **International CAPE is approximate.** No free live API exists for international CAPE. Values are research estimates updated manually.
- **Not financial advice.** These are educational tools for structured thinking. Individual tax situations, liability profiles, and investment horizons require advice from a qualified professional.

---

## Roadmap (planned)

- [ ] Safe Withdrawal Rate calculator (sequence-of-returns risk, FIRE planning)
- [ ] FIRE Number calculator with French tax wrapper optimisation (PEA/AV/CTO)
- [ ] Coast FIRE calculator
- [ ] Historical bootstrapping for international indices (requires sourcing non-US return data)
- [ ] Inflation stress tester (portfolio survival across different inflation regimes)

---

## License

Personal use. Not financial advice.

Data sources: [Robert Shiller](http://www.econ.yale.edu/~shiller/data.htm) · [Aswath Damodaran](https://pages.stern.nyu.edu/~adamodar/) · [FRED / St. Louis Fed](https://fred.stlouisfed.org/) · [StarCapital](https://www.starcapital.de) · Yahoo Finance
