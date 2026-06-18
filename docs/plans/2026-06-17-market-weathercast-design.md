# Market Weathercast — Design

**Date:** 2026-06-17
**Status:** Approved (brainstorming complete)
**Author:** Kris Johnson (with Claude Code)

A new top-level tab in the Stock Value Screener app: a macro-risk dashboard that
reads a set of market-stress indicators over the past two weeks and rolls them
into a single "weathercast" — an overall concern level from 1 (☀️ Sunny) to
5 (🌀 Hurricane) — using free, real data sources.

> Educational tool — not investment advice. Same disclaimer as the screener.

---

## 1. Goals & scope

- Separate **tab** within the existing app so the user moves between the Value
  Screener and the Weathercast (and future tools).
- Pull **real, free data** (no API keys) for every indicator.
- Show each indicator's **current value, status color, and 2-week trend**.
- Roll up into an **overall 1–5 concern level** with a weather metaphor.
- All **ranges/thresholds, weights, and divergence rules are adjustable** and
  **resettable to defaults**.

**In scope (v1 = everything):** VIX, VVIX, SKEW, HY Credit Spreads, 10Y Treasury
(+ yield curve), Gold, Oil (WTI/Brent), Financial Stress (OFR FSI), NFCI, Net
Liquidity, and two custom Crash-Risk indicators (Air Pocket, Cascade).

---

## 2. Decisions (from brainstorming)

| Question | Decision |
|---|---|
| Indicator scope | **Everything**, including custom Crash-Risk (Air Pocket, Cascade) |
| Refresh model | **Auto on tab open + cache** (stale = >30 min) with manual Refresh button |
| Scoring model | **Weighted average + divergence rules** |
| Settings storage | **Backend SQLite** (new table; reset restores defaults from `config.py`) |
| Layout | **Weather hero + indicator cards** with sparklines |
| Sparklines | **Hand-rolled inline SVG** (no new chart dependency) |
| Weather levels | **5 levels:** ☀️ Sunny · 🌤️ Fair · ☁️ Cloudy · ⛈️ Stormy · 🌀 Hurricane |

---

## 3. Architecture

### Frontend
- Wrap the current single screen in an Ant Design `<Tabs>` at the top level of
  `App.tsx`.
  - **Tab 1 — Value Screener:** existing UI moved into a panel, otherwise
    untouched (filters + table + assumptions drawer keep working as-is).
  - **Tab 2 — Market Weathercast:** new components.
- Theme already styles `Tabs`, so no styling work needed.
- New components under `frontend/src/components/market/`:
  - `Weathercast.tsx` — tab container (fetch, staleness, refresh, settings).
  - `WeatherHero.tsx` — headline banner.
  - `IndicatorCard.tsx` — one card per indicator (value, pill, sparkline, trend).
  - `Sparkline.tsx` — tiny inline SVG sparkline with shaded threshold bands.
  - `WeatherSettingsDrawer.tsx` — mirrors `AssumptionsDrawer` (edit/reset).
- New hook `frontend/src/hooks/useWeather.ts` and types in `lib/types.ts`,
  API calls in `lib/api.ts`.

### Backend
- `routers/market.py` — new router.
- `services/market_service.py` — fetch + cache orchestration (calls FRED CSV,
  yfinance, OFR CSV).
- `services/weather.py` — **pure scoring engine** (states → weighted level →
  divergence rules → weather). Unit-tested like `valuation.py`.
- `config.py` — default thresholds, weights, divergence rules, source URLs.
- Two SQLite tables (in `models.py`):
  - `market_snapshot` — `id`, `pulled_at`, `payload` (JSON: raw series + computed
    indicator states + scores). Single latest row (or keep a short history).
  - `market_settings` — `id`, `updated_at`, `payload` (JSON: thresholds + weights
    + divergence toggles). One row; reset clears it back to defaults.

No new ports. No API keys. Docker / docker-export flow unchanged.

---

## 4. Data sources (all free, no keys)

Reuses the two existing patterns: FRED public CSV (`fred_service.py`) and
yfinance (screener). Pull ~30 calendar days of history per series to compute
2-week trends, weekly bps moves, and monthly % changes.

| Indicator | Source | Symbol / series | Notes |
|---|---|---|---|
| VIX | Yahoo (fallback FRED `VIXCLS`) | `^VIX` | 30-day implied vol |
| VVIX | Yahoo | `^VVIX` | vol-of-vol |
| SKEW | Yahoo | `^SKEW` | tail-risk / crash insurance |
| HY Credit Spreads | FRED CSV | `BAMLH0A0HYM2` | ICE BofA US HY OAS (%) |
| 10Y Treasury | FRED CSV | `DGS10` | + `T10Y2Y` for 2s10s curve |
| Gold | Yahoo | `GLD` (or `GC=F`) | % change vs ~1 month |
| Oil WTI | Yahoo | `CL=F` | price level |
| Oil Brent | Yahoo | `BZ=F` | price level |
| NFCI | FRED CSV | `NFCI` | Chicago Fed financial conditions (weekly) |
| Financial Stress | OFR public CSV | OFR FSI daily feed | falls back / optional if feed down |
| Net Liquidity | FRED CSV (derived) | `WALCL − WTREGEN − RRPONTSYD` | Fed assets − TGA − RRP |
| Air Pocket (custom) | Yahoo, derived | `^VIX9D` vs `^VIX` + VIX velocity | see §5 |
| Cascade (custom) | derived | cross-asset + credit + VVIX | see §5 |

**Graceful degradation:** each feed has its own try/except with fallback (same
philosophy as `fetch_aaa_yield`). A failed indicator renders "n/a", greys out,
is excluded from the score, and is visibly marked. The dashboard never 500s.

---

## 5. Indicator definitions

### Threshold-based (from the user's ranges table)
States are **1 (🟢 normal) / 2 (🟡 warning) / 3 (🔴 chaos)**.

| Indicator | 🟢 Green | 🟡 Yellow | 🔴 Red | Basis |
|---|---|---|---|---|
| VIX | <20 | 20–30 | >30 | level |
| VVIX | <90 | 90–110 | >110 | level |
| SKEW | <130 | 130–145 | >145 | level |
| HY Credit Spreads | <4% | 4–6% | >6% | level |
| 10Y move | <15 bps/wk | 15–30 | >30 | weekly change |
| Gold | stable | +5%/mo | +10%/mo | monthly % change |
| Oil | <$90 | $90–110 | >$110 | level |

(NFCI, OFR FSI, Net Liquidity get analogous default bands defined in `config.py`,
editable in the settings drawer.)

### Custom Crash-Risk indicators (transparent + tunable)
- **Air Pocket (near-term gap risk):** fires when the VIX term structure inverts
  (`^VIX9D / ^VIX > 1.0`, near-term fear exceeds 30-day) **and/or** VIX rises
  fast (e.g. > 5 pts over a few days). Output 1–3 with editable trigger
  constants. Reads as "market could gap down on a surprise."
- **Cascade (forced-liquidation / contagion risk):** fires on the
  "everything sold simultaneously" pattern — **stocks ↓ AND bonds ↓ AND gold ↓
  together** (flight-to-quality broken), escalated further when **HY spreads
  widen + VVIX elevated**. Reads as March-2020 / parts-of-2008 contagion.

---

## 6. Scoring model → 1–5 weathercast

1. **Per indicator:** value/change → state 1/2/3 via thresholds.
2. **Base level:** weighted average of states using the user's importance
   ranking as default weights —
   **Credit > Treasuries > SKEW > VVIX > VIX > Gold > Oil**, with composites
   (Financial Stress, Net Liquidity, Crash Risk) weighted in between.
   Normalize the 1–3 weighted average onto **1–5**. All weights editable.
3. **Divergence rules** (bump the base level; each toggleable):
   - **Hidden hedging:** SKEW 🔴 + VVIX ≥🟡 while VIX 🟢 → **+1**
     ("public calm, professionals buying disaster insurance").
   - **Cascade:** stocks ↓ + bonds ↓ + gold ↓ together → **floor at 4**.
   - **Credit + liquidity squeeze:** HY 🔴 + Net Liquidity falling → **+1**.
   - Final level **capped at 5**.
4. **Weather mapping:**
   - 1 → ☀️ **Sunny**
   - 2 → 🌤️ **Fair**
   - 3 → ☁️ **Cloudy**
   - 4 → ⛈️ **Stormy**
   - 5 → 🌀 **Hurricane**

`weather.py` is a **pure function**: `(indicator_states, settings) → {level,
weather, one_line_read, fired_rules}`. No I/O, fully unit-testable.

---

## 7. UI / layout

- **Hero banner (`WeatherHero`):** weather icon + state name + "Concern N/5" +
  one-line plain-English read (e.g. "Surface calm, but credit and
  crash-insurance gauges are flashing"), with **last-updated** time, **Refresh**
  button, and a small color legend.
- **Indicator card grid (responsive):** each `IndicatorCard` shows name, current
  value, 🟢/🟡/🔴 pill, a **2-week SVG sparkline** with shaded threshold bands,
  and the trend (e.g. "+22 bps this week"). Cards ordered by importance ranking.
- **Settings drawer (`WeatherSettingsDrawer`):** edit every threshold, weight,
  and divergence toggle; **Reset to defaults** button.

---

## 8. API surface

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/market/dashboard` | cached snapshot + `stale` flag + computed scores |
| POST | `/api/market/refresh` | re-pull all feeds, recompute, cache, return |
| GET | `/api/market/settings` | current thresholds/weights/rules |
| PUT | `/api/market/settings` | save adjusted settings |
| POST | `/api/market/settings/reset` | restore defaults from `config.py` |

**Flow:** open tab → `GET /dashboard`. If `stale` (>30 min) or user clicks
Refresh → `POST /refresh`. Settings changes recompute scores from the cached
snapshot without re-pulling (same instant-recompute spirit as the screener's
valuation engine).

---

## 9. Error handling

- Per-feed try/except with documented fallback; `/dashboard` and `/refresh`
  never 500 on a single feed failure.
- Failed indicators: rendered "n/a", greyed, excluded from the weighted score,
  and surfaced in the hero read ("2 indicators unavailable").
- Network timeouts mirror `fred_service` (httpx, 15s).

---

## 10. Testing

- **pytest** on `weather.py` with pinned cases:
  - each indicator's threshold → correct state,
  - weighted rollup → expected base level,
  - each divergence rule fires (and only fires) when intended — e.g. the
    "hidden hedging" SPX-calm / SKEW-red case bumps the level by 1; the cascade
    floor sets level 4.
- Mirrors the spirit of `test_valuation.py` (engine pinned to worked examples).
- Light frontend smoke (render hero + a card from a fixture payload).

---

## 11. Out of scope (v1)

- Alerting / notifications.
- Historical archive / charting beyond the 2-week window.
- User accounts (settings are per-container, like Assumptions).
- Background scheduled refresh (explicitly chosen against; auto-on-open instead).
