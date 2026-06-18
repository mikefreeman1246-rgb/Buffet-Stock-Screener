# Stock Value Screener

An S&P 500 value-investing screener built around two intrinsic-value models:

- **Benjamin Graham** — `V = EPS × (8.5 + 2g) × (4.4 / Y)`, with a margin-of-safety
  "sweet spot" and Undervalued → Overvalued verdicts.
- **Warren Buffett** — two-stage owner-earnings DCF with moat-based discount
  rates, plus a justified price-to-book model for banks/insurers, and
  Strong Buy → Pass verdicts.

Both models run side by side with a combined **conviction** flag. Filter the
universe by verdict, conviction, margin of safety, sector, price and market
cap — and **re-rank live** as you adjust global assumptions or per-stock
overrides, with no data re-pull.

The formulas (and every default constant) come from the two reference docs in
the repo root: [`graham-valuation-formula.txt`](graham-valuation-formula.txt)
and [`buffett-modernized-formula.txt`](buffett-modernized-formula.txt).

> Educational tool — not investment advice.

## Data sources (all free, no API keys)

- **yfinance** (Yahoo) — fundamentals, EPS, growth, cash flow (owner earnings).
- **FRED** public CSV — Moody's AAA corporate bond yield (Graham's `Y`).
- **Static S&P 500 seed list** — `backend/app/data/sp500.json`.

There are **no secrets** and no connection to any paid provider. A pluggable
provider seam is left open for a paid upgrade later.

## Architecture

`FastAPI + SQLAlchemy/SQLite` backend, `React + TypeScript + Ant Design`
frontend, Docker-ready. A pull pipeline caches a fundamentals snapshot in
SQLite; the pure **valuation engine** (`backend/app/services/valuation.py`)
recomputes both models from that cache whenever assumptions or overrides change.

## Run — local dev

Backend (Python 3.13):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9000
```

Frontend (Node 20+):

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxies /api to :9000)
```

Then open the app, click **Pull Data → Full S&P 500** to populate the snapshot
(first pull takes a few minutes via Yahoo). Use **Pull Data → Smoke test (10)**
for a quick trial.

## Run — Docker

```bash
docker compose up --build
# frontend: http://localhost:3002   backend: http://localhost:9000
```

## Tests

```bash
cd backend
pytest                # engine pinned to the docs' worked examples
```

The engine tests assert the code reproduces the reference docs exactly —
Graham's Coca-Cola example (`≈ $47.85`), both verdict bands, the Buffett
`g == r` L'Hôpital branch, and the financial P/B model.

## How the screener works

1. **Pull** — fundamentals for the S&P 500 cached to SQLite.
2. **Evaluate** — every stock scored by both models using global *assumptions*
   (bond yield, growth cap, moat discount rates, margin of safety) and optional
   per-stock *overrides* (growth, moat, owner-earnings multiplier, normalized
   EPS for cyclicals).
3. **Filter & rank** — server-side, live (300ms debounce).
4. **Adjust** — change an assumption in the drawer or override a single stock;
   the matching list updates instantly without re-pulling data.

Auto-derived inputs (growth, moat, owner earnings) are **heuristics** and are
clearly labeled as such — expand any row to inspect the full breakdown and
override them to match your own judgment.

## Project layout

```
backend/app/
  services/valuation.py     # pure engine — the heart, fully unit-tested
  services/yfinance_service.py, fred_service.py, pipeline_service.py
  routers/screener.py, stocks.py, assumptions.py, pipeline.py, meta.py
  models.py, database.py, config.py   # config holds doc-sourced defaults
  data/sp500.json
frontend/src/
  components/  Header, ScreenerFilters, ScreenerTable, StockDetail, AssumptionsDrawer
  hooks/       useScreener, usePipeline
  lib/         api, types, format, exportCsv
docs/plans/    design + implementation docs
```
