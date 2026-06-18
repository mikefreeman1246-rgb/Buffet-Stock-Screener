# Stock Value Screener — Design Document

**Date:** 2026-06-11
**Status:** Proposed (awaiting approval)

## Overview

A web application that screens the **S&P 500** through two intrinsic-value
models — **Benjamin Graham's formula** and **Warren Buffett's two-stage
owner-earnings DCF** — and lets the user interactively filter the universe by
each model's output (margin of safety, verdict, discount to intrinsic value)
and **re-screen live** as valuation assumptions are adjusted.

It is a value-investing analogue of the existing Options Screener: same stack,
same dark-teal theme, same live-slider / expandable-table UX — but the filtered
objects are **stocks ranked by intrinsic value**, not options contracts.

This app shares **no API keys, .env, database, or code** with the Options app.
It is a fresh project with its own free data layer.

## Source documents (the spec for the math)

- `buffett-modernized-formula.txt` — Buffett two-stage owner-earnings DCF,
  moat-based discount rates, owner-earnings adjustment, financial-company
  special cases, verdict thresholds.
- `graham-valuation-formula.txt` — Graham `V = EPS × (8.5 + 2g) × (4.4/Y)`,
  margin-of-safety "sweet spot", verdict thresholds.

These two files are the **source of truth** for every formula, constant, and
verdict band below. Any change to the math should be reflected back into them.

## Data sources (all free, no keys)

| Need | Source | Notes |
|---|---|---|
| S&P 500 ticker list | Wikipedia constituents (cached) / static seed list | Refreshable; no key |
| Fundamentals: TTM EPS, ROE, book value, shares out, price, market cap, sector, margins, growth | **yfinance** (Yahoo) | Free, no key. Validated against AAPL. |
| Cash-flow: Free Cash Flow, Capex, D&A (owner earnings) | **yfinance** statements | Free, no key |
| AAA corporate bond yield `Y` (Graham) | **FRED** series `DAAA` via public CSV endpoint | Keyless CSV download; manual override field, default 5.56% |

**No paid APIs.** A pluggable data-provider seam is left in place so a paid
source (e.g. Financial Modeling Prep) can be added later behind the same
interface — but nothing in v1 requires a key.

> Caveat to surface in the UI: yfinance's `earningsGrowth` is a recent
> year-over-year figure, not the 7–10yr forward estimate Graham's `g` ideally
> wants. v1 uses it as the auto default with a **global cap** (Graham's ~20%
> ceiling) and a **per-stock override**. Historical EPS CAGR is offered as an
> alternative auto-source.

## Architecture

**Stack (same as Options app):** FastAPI (Python) + React (TypeScript) +
SQLite + Docker. Ant Design dark-teal theme reused verbatim.

**Pattern:** A weekly/on-demand **pull pipeline** writes a fundamentals
snapshot to SQLite. The **valuation engine** computes Graham + Buffett values
either at pull time (cached) or on demand. The frontend sends filter +
assumption params; the backend recomputes verdicts server-side and returns the
matching, ranked list. WebSocket pushes pull progress (reused pattern).

Crucially, **valuation is cheap and assumption-driven**: changing a global
assumption (bond yield, discount rates, margin %, g cap) re-runs the formulas
over the cached fundamentals **without re-pulling data** — that is what makes
the "adjust and get an updated list" loop instant.

## Database schema

### Table: `stocks` (fundamentals snapshot — raw inputs)
| Column | Type | Source |
|---|---|---|
| ticker | TEXT PK | seed list |
| company | TEXT | yfinance |
| sector | TEXT | yfinance |
| industry | TEXT | yfinance |
| is_financial | BOOLEAN | derived from sector |
| market_cap | REAL | yfinance |
| price | REAL | yfinance |
| eps_ttm | REAL | yfinance `trailingEps` |
| eps_growth | REAL | yfinance `earningsGrowth` (auto `g`) |
| roe | REAL | yfinance |
| book_value_ps | REAL | yfinance |
| shares_out | REAL | yfinance |
| net_income | REAL | yfinance financials |
| dep_amort | REAL | yfinance cashflow |
| capex | REAL | yfinance cashflow |
| free_cash_flow | REAL | yfinance cashflow |
| gross_margin | REAL | yfinance (moat proxy) |
| profit_margin | REAL | yfinance (moat proxy) |
| updated_at | DATETIME | |

### Table: `overrides` (per-stock manual judgment)
| Column | Type | Notes |
|---|---|---|
| ticker | TEXT PK FK | |
| growth_override | REAL NULL | overrides auto `g` |
| moat_override | TEXT NULL | wide/moderate/narrow/none |
| oe_multiplier_override | REAL NULL | overrides auto owner-earnings multiplier |
| normalized_eps_override | REAL NULL | for cyclicals (doc Mod #4c) |
| note | TEXT NULL | |
| updated_at | DATETIME | |

### Table: `assumptions` (single-row global settings)
| Column | Type | Default (from docs) |
|---|---|---|
| aaa_bond_yield | REAL | 5.56 |
| graham_base_pe | REAL | 8.5 |
| graham_growth_multiplier | REAL | 2.0 |
| graham_g_cap | REAL | 20 |
| margin_of_safety_pct | REAL | 0.25 |
| r_wide / r_moderate / r_narrow / r_none | REAL | 8.5 / 9.5 / 10.5 / 11.5 |
| terminal_growth | REAL | 2.5 |
| high_growth_years | INT | 10 |

### Table: `pull_status`
Reused from Options app (pull_type, status, totals, checkpoint, timestamps).

## Valuation engine (`services/valuation.py`)

Pure functions, fully unit-tested against the worked examples in the docs
(e.g. Graham KO ≈ $47.85; Buffett verdict bands).

### Graham
```
g_eff   = min(growth_override ?? eps_growth, g_cap)
mult    = base_pe + growth_multiplier * g_eff
adj     = 4.4 / aaa_bond_yield
V_graham = eps_ttm * mult * adj
sweet_spot = V_graham * (1 - margin_of_safety_pct)
```
Verdict bands (price vs V_graham): <85% Undervalued, 85–110% Fair,
110–135% Mild Overvalued, >135% Overvalued. Negative/near-zero EPS → "N/A
(Graham fails)" flag, per the doc's known limitations.

### Buffett
```
OE_ps   = owner_earnings_per_share (see below)
g       = growth (capped), r = discount rate from moat
Stage 1 = OE * [1 - ((1+g)/(1+r))^N] / (r - g)   (L'Hôpital limit if g==r)
Stage 2 = OE*(1+g)^N * (1+tg) / [(r - tg) * (1+r)^N]
V_buffett = Stage1 + Stage2
ratio = V_buffett / price ; moat bonus (wide +5%, moderate +2%)
```
Verdict bands (adjusted ratio): ≥1.50 Strong Buy, 1.20–1.49 Buy,
0.92–1.19 Hold, 0.78–0.91 Trim, <0.78 Pass.

**Owner earnings (auto):** `OE = net_income + dep_amort − maintenance_capex`,
with maintenance capex approximated as `min(capex, dep_amort)` (conservative);
fall back to Free Cash Flow when statement rows are missing. `oe_multiplier =
OE / net_income`, overridable per stock.

**Moat (auto proxy, overridable):** classified from ROE + margins —
e.g. Wide if ROE>20% & gross margin>50% & profit margin>15%; Moderate / Narrow
by descending thresholds; None below. Clearly labeled as a heuristic proxy.

**Financial companies (sector flag) — IN v1:** Graham/DCF flagged as
unreliable per doc Mod #4. For banks/insurers (Financial Services sector), the
Buffett-side value uses the **justified price-to-book anchor**:
`fair_P/B = (ROE − g)/(r − g)`, `V = fair_P/B × book_value_ps`. The table marks
these rows as P/B-valued so the user knows the method differs. EPS-based
Graham/DCF values are still shown but tagged low-confidence for financials.

### Dual conviction (doc "use both and compare")
Combine the two verdicts into a conviction flag: Graham-Undervalued +
Buffett-Buy/Strong-Buy → "Max conviction"; both overvalued → "Avoid"; etc.

## Backend API

- `POST /api/pipeline/start` · `/resume` · `/stop` · `GET /status` — data pull
- `GET /api/screener` — main endpoint. Query params: model (graham/buffett/dual),
  sector[], verdict[], min_margin_of_safety, price range, market-cap range,
  search, sort, pagination. **Plus assumption overrides** (bond yield, g cap,
  margin %, discount rates) so the list recomputes live without a re-pull.
- `GET /api/stocks/{ticker}` — full valuation breakdown (both models, every
  intermediate term) for the expanded row / detail.
- `PUT /api/stocks/{ticker}/override` — set per-stock g/moat/OE/normalized EPS.
- `GET/PUT /api/assumptions` — global assumptions.
- `GET /api/meta/last-refresh` · `/stats` — snapshot freshness.

## Frontend

**Single screener view** (cleaner than splitting models across tabs):

- **Header** (reused): title, last-refresh status dot, refresh button + inline
  pipeline progress.
- **Global Assumptions drawer** (reused PipelineDrawer pattern): sliders/inputs
  for bond yield `Y`, `g` cap, margin-of-safety %, the four moat discount rates,
  terminal growth. Editing any of these instantly re-screens.
- **Filter bar:** model toggle (Graham / Buffett / Dual), verdict multi-select,
  min margin-of-safety slider, sector multi-select, price & market-cap ranges,
  ticker search. Debounced live re-filtering; live result count.
- **Results table:** Ticker · Company · Sector · Price · Graham Value ·
  Graham margin · Graham verdict · Buffett Value · Buffett verdict · Conviction.
  Color-coded verdict tags reusing the theme's success/warning/error tokens.
- **Expandable row:** full valuation breakdown — every intermediate term for
  both models — plus inline **per-stock override** controls (g, moat,
  owner-earnings multiplier, normalized EPS) that recompute that row instantly.
- **CSV export** (reused `exportCsv.ts`).

## Reused vs new

**Reused (theme/UX, adapted):** App shell + dark theme, Header, PipelineDrawer,
FloatingActionBar, PresetDropdown, useFilters/useFilterPresets/usePipeline
hooks, api.ts client, exportCsv.ts, WebSocket pipeline pattern, DB/pull_status
pattern.

**New:** yfinance + FRED data services, valuation engine, screener router,
assumptions + overrides tables/endpoints, screener table & assumptions UI.

**Dropped:** all Marketdata/Tastytrade/options/earnings/LLM-research code, all
existing keys and .env.

## Project structure

```
Stock_Screener/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py, config.py, database.py, models.py, websocket.py
│   │   ├── routers/  (pipeline, screener, stocks, assumptions, meta)
│   │   └── services/ (yfinance_service, fred_service, valuation, pipeline_service)
│   ├── requirements.txt   (fastapi, sqlalchemy, yfinance, pandas, httpx, ...)
│   └── tests/  (valuation tests vs doc worked-examples)
├── frontend/  (Vite + React + antd; theme copied from Options app)
├── data/  (stock_screener.db)
├── docs/plans/  (this doc + implementation plan)
└── .env.example  (no secrets; only optional future provider key)
```

## Verification

- Unit tests assert the engine reproduces the docs' worked examples
  (Graham KO ≈ $47.85 within rounding; Buffett verdict bands; Graham verdict
  bands; L'Hôpital g==r branch).
- A smoke pull of ~10 tickers confirms the yfinance + FRED path end to end.

## Resolved decisions (2026-06-11)

1. **Financial-company P/B model — IN v1.** Justified P/B anchor for
   banks/insurers (see Buffett engine section).
2. **Universe — static seed S&P 500 list** committed as JSON, with a manual
   "refresh list" action available later.
3. **g source default — yfinance `earningsGrowth`**, capped at the Graham `g`
   ceiling (20). Historical EPS CAGR offered as an alternative auto-source and
   as a fallback when `earningsGrowth` is missing.

## Out of scope (v1)

Paid data providers, options/earnings, LLM research, portfolio tracking,
backtesting. The data-provider seam keeps a paid upgrade path open.

---
*Not investment advice. Educational tool. Source math: the two formula docs in
this folder.*
