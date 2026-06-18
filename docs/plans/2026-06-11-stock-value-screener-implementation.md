# Stock Value Screener — Implementation Plan

**Date:** 2026-06-11
**Design:** `2026-06-11-stock-value-screener-design.md`
**Approach:** Backend-first. Engine is unit-tested against the formula docs'
worked examples *before* any UI work.

## Phase 0 — Scaffold
- [ ] `backend/` skeleton: `app/{main,config,database,models,websocket}.py`,
  `routers/`, `services/`, `tests/`, `requirements.txt`, `run.py`, `Dockerfile`.
- [ ] `frontend/` from Vite React-TS template; copy theme tokens + Header/shell
  from Options app; strip options/earnings code.
- [ ] `docker-compose.yml`, `.env.example` (no secrets), `.gitignore`,
  `data/` dir. `git init`.
- [ ] Seed: `backend/app/data/sp500.json` (ticker, company, sector).

## Phase 1 — Data services (free, no keys)
- [ ] `services/fred_service.py` — fetch AAA yield from FRED public CSV
  (`fredgraph.csv?id=DAAA`), parse latest value, cache, fallback 5.56.
- [ ] `services/yfinance_service.py` — per-ticker fundamentals + cash-flow
  extraction into a typed dict matching the `stocks` schema. Robust to missing
  fields (None, not crash). Historical EPS CAGR helper.
- [ ] `services/pipeline_service.py` — iterate seed list with bounded
  concurrency, upsert snapshot, checkpoint `pull_status`, push WS progress.
- [ ] Smoke test: pull ~10 tickers end to end, inspect DB.

## Phase 2 — Valuation engine (PURE, TESTED FIRST)
- [ ] `services/valuation.py` — pure functions: `graham_value`,
  `graham_verdict`, `owner_earnings`, `moat_classify`, `buffett_value`
  (incl. `g==r` L'Hôpital branch), `buffett_verdict`, `financial_pb_value`,
  `dual_conviction`. No I/O; takes fundamentals + assumptions + overrides.
- [ ] `tests/test_valuation.py` FIRST:
  - Graham KO worked example ≈ $47.85 (EPS 2.95, g 6, Y 5.56).
  - Graham multiplier table (g=0→8.5 … g=20→48.5).
  - Graham verdict bands (85/110/135%).
  - Buffett `g==r` limit branch equals the L'Hôpital formula.
  - Buffett verdict bands (1.50/1.20/0.92/0.78) + moat bonus.
  - Negative-EPS Graham → N/A flag.
  - Financial P/B `(ROE−g)/(r−g)`.
- [ ] Implement until green.

## Phase 3 — API
- [ ] `models.py` + `database.py`: `stocks`, `overrides`, `assumptions`
  (single row, seeded with doc defaults), `pull_status`. Init + light migrate.
- [ ] `routers/assumptions.py` — GET/PUT global assumptions.
- [ ] `routers/screener.py` — GET `/api/screener`: load snapshot, apply
  overrides + assumptions (from query or stored), compute both models in the
  engine, filter (model, verdict[], sector[], min MoS, price/cap, search),
  sort, paginate.
- [ ] `routers/stocks.py` — GET `/{ticker}` full breakdown;
  PUT `/{ticker}/override`.
- [ ] `routers/pipeline.py` + `routers/meta.py` + `websocket.py` — adapt from
  Options app.
- [ ] Wire routers in `main.py`; `/api/health`.

## Phase 4 — Frontend
- [ ] `lib/api.ts` typed client; `lib/exportCsv.ts` reused.
- [ ] `AssumptionsDrawer` — global sliders/inputs; PUT + re-screen.
- [ ] `ScreenerFilters` — model toggle, verdict multi-select, MoS slider,
  sector multi-select, price/cap ranges, search (debounced).
- [ ] `ScreenerTable` — columns per design; color-coded verdict tags;
  expandable row with full breakdown + per-stock override controls.
- [ ] `Header` reused — refresh button + WS pipeline progress + freshness dot.
- [ ] CSV export button.

## Phase 5 — Verify & polish
- [ ] Full S&P 500 pull; spot-check a handful vs doc expectations.
- [ ] `npm run build` + backend `pytest` green.
- [ ] README with run instructions (dev + docker).

## Order of build
Phase 0 → 1 → **2 (tests-first)** → 3 → 4 → 5.
The valuation engine is the heart; it is proven correct against the docs before
anything depends on it.
