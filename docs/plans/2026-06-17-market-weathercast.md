# Market Weathercast Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a second top-level tab to the Stock Screener app — a "Market Weathercast" macro-risk dashboard that pulls free market-stress data, scores each indicator, and rolls them into an overall 1–5 concern level (☀️ Sunny → 🌀 Hurricane).

**Architecture:** A pure scoring engine (`weather.py`, TDD-first) consumes per-indicator metrics from data services (FRED CSV + yfinance + OFR CSV), applies user-adjustable thresholds/weights and divergence rules, and emits a weather state. A new FastAPI router caches the latest snapshot and settings in SQLite. The React app wraps its current screen in Ant Design `<Tabs>` and adds a weather dashboard (hero + indicator cards + settings drawer).

**Tech Stack:** FastAPI · SQLAlchemy/SQLite · httpx · yfinance · pytest (backend); React + TypeScript + Ant Design + axios (frontend). No new ports, no API keys, no new chart dependency (inline SVG sparklines).

---

## Conventions & notes for the implementer

- **Read first** (do not skip — match these patterns exactly):
  - `backend/app/services/fred_service.py` — the FRED-CSV + graceful-fallback pattern every fetcher mirrors.
  - `backend/app/services/valuation.py` + `backend/tests/test_valuation.py` — the "pure engine, pinned tests" style `weather.py` follows.
  - `backend/app/routers/assumptions.py` — router + Pydantic + `_serialize` pattern.
  - `backend/app/config.py`, `backend/app/models.py`, `backend/app/database.py` — where defaults/tables/seed live.
  - `frontend/src/App.tsx`, `frontend/src/lib/api.ts`, `frontend/src/components/AssumptionsDrawer.tsx` — frontend patterns.
- **Run backend tests:** `cd backend && pytest -v`
- **Run the app to verify:** `docker compose -f docker-compose.yml -f docker-compose.dev-ports.yml up --build` (frontend :3002, backend :9000), or local dev per README.
- **Git:** this project is **not** a git repo today. If you want commits, run `git init` first; otherwise treat each "Commit" step as a checkpoint to run tests and confirm green before moving on.
- **DRY / YAGNI / TDD:** the engine and config are fully test-driven. Services degrade gracefully and never raise (like `fetch_aaa_yield`).
- **Uniform metric direction:** every indicator's `metric` is normalized so **higher = more stress** (Net Liquidity is inverted by the service before scoring). This keeps `weather.py` thresholds one-directional and simple.

---

## Phase 1 — Scoring engine + config defaults (backend, TDD)

### Task 1: Default thresholds, weights, divergence rules, and source URLs in `config.py`

**Files:**
- Modify: `backend/app/config.py` (append a new section at the end)

**Step 1: Add the weather config block**

Append to `backend/app/config.py`:

```python
# ---------------------------------------------------------------------------
# Market Weathercast
# ---------------------------------------------------------------------------
# All free, no-API-key sources. FRED public CSV + Yahoo (yfinance) + OFR CSV.
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
MARKET_FRED_SERIES = {
    "credit": "BAMLH0A0HYM2",   # ICE BofA US High Yield OAS (%)
    "dgs10": "DGS10",           # 10Y Treasury yield (%)
    "t10y2y": "T10Y2Y",         # 2s10s curve (%)
    "nfci": "NFCI",             # Chicago Fed financial conditions (weekly)
    "walcl": "WALCL",           # Fed total assets ($MM, weekly)
    "tga": "WTREGEN",           # Treasury General Account ($BN, weekly)
    "rrp": "RRPONTSYD",         # Overnight reverse repo ($BN, daily)
}
MARKET_YF_SYMBOLS = {
    "vix": "^VIX", "vvix": "^VVIX", "skew": "^SKEW", "vix9d": "^VIX9D",
    "gold": "GLD", "wti": "CL=F", "brent": "BZ=F", "spx": "^GSPC", "tlt": "TLT",
}
OFR_FSI_CSV = "https://www.financialresearch.gov/financial-stress-index/data/fsi.csv"

MARKET_STALE_SECONDS = 30 * 60  # auto-refresh when snapshot older than 30 min

# Each indicator's metric is normalized so HIGHER = MORE STRESS.
# green: metric <= green_max ; yellow: <= yellow_max ; red: above yellow_max.
DEFAULT_WEATHER_SETTINGS = {
    "thresholds": {
        # key:            label                weight green_max yellow_max  unit
        "credit":   {"label": "HY Credit Spreads", "weight": 7, "green_max": 4.0,  "yellow_max": 6.0,  "unit": "%"},
        "cascade":  {"label": "Cascade Risk",       "weight": 6, "green_max": 1.0,  "yellow_max": 2.0,  "unit": ""},
        "treasuries":{"label":"10Y Move (bps/wk)",  "weight": 6, "green_max": 15.0, "yellow_max": 30.0, "unit": "bps"},
        "net_liquidity":{"label":"Net Liquidity",   "weight": 5, "green_max": 1.0,  "yellow_max": 2.0,  "unit": ""},
        "financial_stress":{"label":"OFR Fin. Stress","weight":5,"green_max": 0.0,  "yellow_max": 1.0,  "unit": ""},
        "skew":     {"label": "SKEW",               "weight": 5, "green_max": 130.0,"yellow_max": 145.0,"unit": ""},
        "nfci":     {"label": "NFCI",               "weight": 4, "green_max": -0.2, "yellow_max": 0.0,  "unit": ""},
        "vvix":     {"label": "VVIX",               "weight": 4, "green_max": 90.0, "yellow_max": 110.0,"unit": ""},
        "air_pocket":{"label":"Air Pocket Risk",    "weight": 4, "green_max": 1.0,  "yellow_max": 2.0,  "unit": ""},
        "vix":      {"label": "VIX",                "weight": 3, "green_max": 20.0, "yellow_max": 30.0, "unit": ""},
        "gold":     {"label": "Gold (% / mo)",      "weight": 2, "green_max": 5.0,  "yellow_max": 10.0, "unit": "%"},
        "oil":      {"label": "Oil (WTI)",          "weight": 1, "green_max": 90.0, "yellow_max": 110.0,"unit": "$"},
    },
    "rules": {
        "hidden_hedging": True,    # SKEW red + VVIX>=yellow while VIX green -> +1
        "credit_liquidity": True,  # credit red + net liquidity tight -> +1
        "cascade_floor": True,     # stocks+bonds+gold all down -> floor at 4
    },
}
```

**Step 2: Sanity check it imports**

Run: `cd backend && python -c "from app.config import DEFAULT_WEATHER_SETTINGS; print(len(DEFAULT_WEATHER_SETTINGS['thresholds']))"`
Expected: `12`

**Step 3: Commit** — `feat(config): weather indicator defaults, weights, rules, sources`

---

### Task 2: Pure scoring engine `weather.py` — classify + weighted base

**Files:**
- Create: `backend/app/services/weather.py`
- Test: `backend/tests/test_weather.py`

**Step 1: Write the failing tests**

Create `backend/tests/test_weather.py`:

```python
from app.config import DEFAULT_WEATHER_SETTINGS
from app.services import weather


def s(metrics, **signals):
    """Build an indicators dict: {key: {"metric": v}} plus cascade signals."""
    ind = {k: {"metric": v} for k, v in metrics.items()}
    if signals:
        ind.setdefault("cascade", {})
        ind["cascade"].update(signals)
    return ind


def test_classify_bands():
    assert weather.classify(10.0, 20.0, 30.0) == weather.GREEN
    assert weather.classify(25.0, 20.0, 30.0) == weather.YELLOW
    assert weather.classify(35.0, 20.0, 30.0) == weather.RED
    assert weather.classify(None, 20.0, 30.0) is None


def test_all_green_is_sunny():
    metrics = {k: c["green_max"] for k, c in DEFAULT_WEATHER_SETTINGS["thresholds"].items()}
    out = weather.score(s(metrics), DEFAULT_WEATHER_SETTINGS)
    assert out["level"] == 1
    assert out["weather"] == "Sunny"


def test_all_red_is_hurricane():
    metrics = {k: c["yellow_max"] + 100 for k, c in DEFAULT_WEATHER_SETTINGS["thresholds"].items()}
    out = weather.score(s(metrics), DEFAULT_WEATHER_SETTINGS)
    assert out["level"] == 5
    assert out["weather"] == "Hurricane"


def test_missing_indicator_excluded():
    # only VIX present and green -> still sunny, no crash
    out = weather.score({"vix": {"metric": 12.0}}, DEFAULT_WEATHER_SETTINGS)
    assert out["level"] == 1
    assert out["states"]["credit"] is None
```

**Step 2: Run to verify they fail**

Run: `cd backend && pytest tests/test_weather.py -v`
Expected: FAIL (`ModuleNotFoundError: app.services.weather`)

**Step 3: Implement `weather.py`**

Create `backend/app/services/weather.py`:

```python
"""Pure market-weather scoring engine. No I/O — fully unit-testable.

Consumes per-indicator metrics (normalized so HIGHER = MORE STRESS) plus the
active settings (thresholds/weights/rules) and returns an overall 1-5 concern
level mapped to a weather state, with the divergence rules that fired.
"""
from __future__ import annotations

GREEN, YELLOW, RED = 1, 2, 3

WEATHER = {
    1: ("Sunny", "☀️"),
    2: ("Fair", "🌤️"),
    3: ("Cloudy", "☁️"),
    4: ("Stormy", "⛈️"),
    5: ("Hurricane", "🌀"),
}


def classify(metric: float | None, green_max: float, yellow_max: float) -> int | None:
    """Map a stress metric to GREEN/YELLOW/RED (None if no data)."""
    if metric is None:
        return None
    if metric <= green_max:
        return GREEN
    if metric <= yellow_max:
        return YELLOW
    return RED


def score(indicators: dict, settings: dict) -> dict:
    """indicators: {key: {"metric": float|None, ...}}; settings: DEFAULT_WEATHER_SETTINGS shape."""
    thr = settings["thresholds"]
    rules = settings.get("rules", {})

    states = {
        key: classify(indicators.get(key, {}).get("metric"),
                      cfg["green_max"], cfg["yellow_max"])
        for key, cfg in thr.items()
    }

    num = den = 0.0
    for key, cfg in thr.items():
        st = states[key]
        if st is None:
            continue
        num += cfg["weight"] * st
        den += cfg["weight"]
    base = 1.0 if den == 0 else 1.0 + (num / den - 1.0) * 2.0  # 1..3 -> 1..5

    level = base
    fired: list[str] = []

    if rules.get("hidden_hedging") and (
        states.get("skew") == RED
        and states.get("vvix") in (YELLOW, RED)
        and states.get("vix") == GREEN
    ):
        level += 1
        fired.append("hidden_hedging")

    if rules.get("credit_liquidity") and (
        states.get("credit") == RED and states.get("net_liquidity") in (YELLOW, RED)
    ):
        level += 1
        fired.append("credit_liquidity")

    if rules.get("cascade_floor"):
        c = indicators.get("cascade", {})
        if c.get("stocks_down") and c.get("bonds_down") and c.get("gold_down"):
            level = max(level, 4)
            fired.append("cascade_floor")

    final = max(1, min(5, round(level)))
    name, icon = WEATHER[final]
    return {
        "level": final,
        "weather": name,
        "icon": icon,
        "base": round(base, 2),
        "states": states,
        "fired_rules": fired,
        "missing": [k for k, v in states.items() if v is None],
        "read": _read(final, states, fired),
    }


def _read(level: int, states: dict, fired: list[str]) -> str:
    """One-line plain-English summary for the hero banner."""
    reds = [k for k, v in states.items() if v == RED]
    if "hidden_hedging" in fired:
        return "Surface calm, but professionals are buying crash insurance (SKEW/VVIX elevated while VIX low)."
    if "cascade_floor" in fired:
        return "Stocks, bonds and gold falling together — flight-to-quality broken."
    if level <= 1:
        return "Conditions calm across the board."
    if level == 2:
        return "Mostly calm with a few gauges ticking up."
    if level == 3:
        return f"Choppy — watching {', '.join(reds) or 'several gauges'}."
    if level == 4:
        return f"Stormy — {len(reds)} gauges flashing red."
    return "Crisis conditions — broad, simultaneous stress."
```

**Step 4: Run tests to verify pass**

Run: `cd backend && pytest tests/test_weather.py -v`
Expected: PASS (4 tests)

**Step 5: Commit** — `feat(weather): pure scoring engine (classify + weighted base)`

---

### Task 3: Divergence-rule tests (the "smart" part)

**Files:**
- Modify: `backend/tests/test_weather.py`

**Step 1: Add rule tests**

Append to `backend/tests/test_weather.py`:

```python
def test_hidden_hedging_bumps_level():
    # VIX calm (green), but SKEW red + VVIX yellow -> +1 over the calm base
    metrics = {"vix": 14.0, "skew": 150.0, "vvix": 100.0}
    out = weather.score(s(metrics), DEFAULT_WEATHER_SETTINGS)
    assert "hidden_hedging" in out["fired_rules"]
    base_only = weather.score(
        s({"vix": 14.0}), DEFAULT_WEATHER_SETTINGS  # control without hedging combo
    )
    assert out["level"] > base_only["level"]


def test_hidden_hedging_does_not_fire_when_vix_high():
    metrics = {"vix": 35.0, "skew": 150.0, "vvix": 100.0}
    out = weather.score(s(metrics), DEFAULT_WEATHER_SETTINGS)
    assert "hidden_hedging" not in out["fired_rules"]


def test_cascade_floor_sets_min_level_4():
    metrics = {"vix": 12.0}  # otherwise calm
    out = weather.score(s(metrics, stocks_down=True, bonds_down=True, gold_down=True),
                        DEFAULT_WEATHER_SETTINGS)
    assert out["level"] >= 4
    assert "cascade_floor" in out["fired_rules"]


def test_rules_can_be_disabled():
    settings = {**DEFAULT_WEATHER_SETTINGS,
                "rules": {"hidden_hedging": False, "credit_liquidity": False, "cascade_floor": False}}
    metrics = {"vix": 14.0, "skew": 150.0, "vvix": 100.0}
    out = weather.score(s(metrics), settings)
    assert out["fired_rules"] == []
```

**Step 2: Run** — `cd backend && pytest tests/test_weather.py -v` → Expected: PASS (8 tests)

**Step 3: Commit** — `test(weather): divergence rules fire and toggle correctly`

---

## Phase 2 — Data fetch services (backend)

### Task 4: FRED multi-series history fetcher

**Files:**
- Create: `backend/app/services/market_fred.py`

**Step 1: Implement** (mirrors `fred_service.py` — never raises)

```python
"""Fetch recent history for arbitrary FRED series via public CSV (no API key)."""
from __future__ import annotations

import csv
import io
import logging

import httpx

from app.config import FRED_CSV

log = logging.getLogger(__name__)


async def fetch_series(series_id: str, days: int = 45) -> list[tuple[str, float]]:
    """Return [(date, value)] for the last ~`days` observations. Never raises."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(FRED_CSV.format(series=series_id))
            resp.raise_for_status()
        return _parse(resp.text)[-days:]
    except Exception as exc:  # noqa: BLE001 — degrade gracefully
        log.warning("FRED %s fetch failed (%s)", series_id, exc)
        return []


def _parse(csv_text: str) -> list[tuple[str, float]]:
    rows = list(csv.reader(io.StringIO(csv_text)))
    out: list[tuple[str, float]] = []
    for row in rows[1:]:
        if len(row) < 2:
            continue
        raw = row[-1].strip()
        if raw in ("", "."):
            continue
        try:
            out.append((row[0], float(raw)))
        except ValueError:
            continue
    return out
```

**Step 2: Smoke test** — `cd backend && python -c "import asyncio; from app.services.market_fred import fetch_series; print(asyncio.run(fetch_series('DGS10'))[-3:])"`
Expected: a list of 3 recent `(date, value)` tuples (or `[]` if offline).

**Step 3: Commit** — `feat(market): FRED multi-series history fetcher`

---

### Task 5: yfinance market-history fetcher

**Files:**
- Create: `backend/app/services/market_yf.py`

**Step 1: Implement** (mirror how `yfinance_service.py` calls yfinance; never raises)

```python
"""Fetch ~6 weeks of daily closes for market symbols via yfinance. Never raises."""
from __future__ import annotations

import logging

import yfinance as yf

log = logging.getLogger(__name__)


def fetch_closes(symbols: dict[str, str], period: str = "2mo") -> dict[str, list[float]]:
    """symbols: {key: yahoo_symbol} -> {key: [close, ...]} oldest..newest. Missing -> []."""
    out: dict[str, list[float]] = {}
    for key, sym in symbols.items():
        try:
            hist = yf.Ticker(sym).history(period=period)
            closes = [float(x) for x in hist["Close"].dropna().tolist()]
            out[key] = closes
        except Exception as exc:  # noqa: BLE001
            log.warning("yfinance %s (%s) failed: %s", key, sym, exc)
            out[key] = []
    return out
```

**Step 2: Smoke test** — `cd backend && python -c "from app.services.market_yf import fetch_closes; d=fetch_closes({'vix':'^VIX'}); print(len(d['vix']))"`
Expected: a number > 20 (or 0 if offline/symbol unavailable).

**Step 3: Commit** — `feat(market): yfinance closes fetcher`

---

### Task 6: Indicator assembly + metric normalization (`market_service.py`)

This is the orchestration layer: pull everything, compute each indicator's **stress metric** (higher = worse), the 2-week sparkline series, the trend label, and the cascade signal booleans. Output feeds straight into `weather.score`.

**Files:**
- Create: `backend/app/services/market_service.py`
- Test: `backend/tests/test_market_metrics.py`

**Step 1: Write failing tests for the pure metric helpers**

Create `backend/tests/test_market_metrics.py`:

```python
from app.services import market_service as m


def test_pct_change_month():
    # ~21 trading days; +10% from first to last
    series = [100.0] * 21 + [110.0]
    assert round(m.pct_change(series, lookback=21), 1) == 10.0


def test_bps_change_week():
    # yield 4.00 -> 4.25 over 5 sessions = +25 bps
    series = [4.00, 4.05, 4.10, 4.15, 4.20, 4.25]
    assert round(m.bps_change(series, lookback=5), 0) == 25.0


def test_net_liquidity_metric_inverts_direction():
    # Net liquidity FALLING should yield a HIGHER stress metric.
    falling = m.net_liquidity_metric(walcl=[8.0, 7.0], tga=[0.5, 0.5], rrp=[0.5, 0.5])
    rising = m.net_liquidity_metric(walcl=[7.0, 8.0], tga=[0.5, 0.5], rrp=[0.5, 0.5])
    assert falling > rising


def test_last_safe():
    assert m.last([]) is None
    assert m.last([1.0, 2.0]) == 2.0
```

**Step 2: Run** → Expected: FAIL (`market_service` missing helpers)

**Step 3: Implement `market_service.py`**

Create `backend/app/services/market_service.py`:

```python
"""Pull all weather inputs, normalize to stress metrics, assemble indicators.

Every indicator dict has: metric (higher=worse, None if no data), value (raw,
for display), series (last ~14 points for the sparkline), trend (label string).
Cascade additionally carries stocks_down / bonds_down / gold_down booleans.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.config import (MARKET_FRED_SERIES, MARKET_YF_SYMBOLS, OFR_FSI_CSV)
from app.services.market_fred import fetch_series
from app.services.market_yf import fetch_closes

import httpx
import logging

log = logging.getLogger(__name__)
SPARK = 14  # sparkline length (~2 weeks of sessions)


# --- pure helpers (unit-tested) -------------------------------------------
def last(series: list[float]) -> float | None:
    return series[-1] if series else None


def pct_change(series: list[float], lookback: int) -> float | None:
    if len(series) <= lookback or series[-1 - lookback] == 0:
        return None
    return (series[-1] / series[-1 - lookback] - 1.0) * 100.0


def bps_change(series: list[float], lookback: int) -> float | None:
    if len(series) <= lookback:
        return None
    return (series[-1] - series[-1 - lookback]) * 100.0  # yield pts -> bps


def net_liquidity_metric(walcl: list[float], tga: list[float], rrp: list[float]) -> float | None:
    """Net liquidity = Fed assets - TGA - RRP. Return a stress metric where a
    FALLING 4-week trend scores higher (tighter = more stress)."""
    n = min(len(walcl), len(tga), len(rrp))
    if n < 2:
        return None
    nl = [walcl[-i] - tga[-i] - rrp[-i] for i in range(1, n + 1)][::-1]
    look = min(20, len(nl) - 1)
    change = nl[-1] - nl[-1 - look]
    # map: big drop -> ~3, flat -> ~1, rising -> <1 (clamped later by thresholds)
    return 2.0 - (change / (abs(nl[-1]) or 1.0)) * 10.0


# --- assembly --------------------------------------------------------------
async def assemble_indicators() -> dict:
    yf = fetch_closes(MARKET_YF_SYMBOLS)
    fred = {key: [v for _, v in await fetch_series(series)]
            for key, series in MARKET_FRED_SERIES.items()}
    ofr = await _fetch_ofr()

    ind: dict[str, dict] = {}

    def card(metric, value, series, trend):
        return {"metric": metric, "value": value,
                "series": (series or [])[-SPARK:], "trend": trend}

    # Yahoo level indicators
    ind["vix"] = card(last(yf["vix"]), last(yf["vix"]), yf["vix"], _spark_trend(yf["vix"]))
    ind["vvix"] = card(last(yf["vvix"]), last(yf["vvix"]), yf["vvix"], _spark_trend(yf["vvix"]))
    ind["skew"] = card(last(yf["skew"]), last(yf["skew"]), yf["skew"], _spark_trend(yf["skew"]))
    ind["oil"] = card(last(yf["wti"]), last(yf["wti"]), yf["wti"], _spark_trend(yf["wti"]))
    gold_mo = pct_change(yf["gold"], 21)
    ind["gold"] = card(gold_mo, last(yf["gold"]), yf["gold"],
                       (f"{gold_mo:+.1f}% / mo" if gold_mo is not None else "n/a"))

    # FRED indicators
    ind["credit"] = card(last(fred["credit"]), last(fred["credit"]), fred["credit"], _spark_trend(fred["credit"]))
    move = bps_change(fred["dgs10"], 5)
    ind["treasuries"] = card(move, last(fred["dgs10"]), fred["dgs10"],
                             (f"{move:+.0f} bps / wk" if move is not None else "n/a"))
    ind["nfci"] = card(last(fred["nfci"]), last(fred["nfci"]), fred["nfci"], _spark_trend(fred["nfci"]))
    ind["net_liquidity"] = card(
        net_liquidity_metric(fred["walcl"], fred["tga"], fred["rrp"]),
        None, fred["walcl"], "4-wk trend")
    ind["financial_stress"] = card(last(ofr), last(ofr), ofr, _spark_trend(ofr))

    # Custom crash-risk
    ind["air_pocket"] = _air_pocket(yf)
    ind["cascade"] = _cascade(yf, fred)
    return ind


def _spark_trend(series: list[float]) -> str:
    if len(series) < 2 or series[-1 - min(5, len(series) - 1)] == 0:
        return "n/a"
    pct = (series[-1] / series[-1 - min(5, len(series) - 1)] - 1.0) * 100.0
    return f"{pct:+.1f}% / wk"


def _air_pocket(yf: dict) -> dict:
    """Near-term gap risk: VIX9D/VIX term-structure inversion + VIX velocity."""
    vix, vix9d = yf.get("vix", []), yf.get("vix9d", [])
    if not vix or not vix9d:
        return {"metric": None, "value": None, "series": [], "trend": "n/a"}
    ratio = vix9d[-1] / vix[-1] if vix[-1] else 1.0
    velocity = (vix[-1] - vix[-1 - min(3, len(vix) - 1)]) if len(vix) > 1 else 0.0
    metric = 1.0
    if ratio > 1.0 or velocity > 5:
        metric = 2.0
    if ratio > 1.05 or velocity > 8:
        metric = 3.0
    series = [a / b for a, b in zip(vix9d[-14:], vix[-14:]) if b]
    return {"metric": metric, "value": round(ratio, 2), "series": series,
            "trend": f"9D/30D {ratio:.2f}"}


def _cascade(yf: dict, fred: dict) -> dict:
    """Contagion: stocks+bonds+gold down together, worse on credit/VVIX stress."""
    def falling(series, look=5):
        return bool(series) and len(series) > look and series[-1] < series[-1 - look]

    stocks_down = falling(yf.get("spx", []))
    bonds_down = falling(yf.get("tlt", []))
    gold_down = falling(yf.get("gold", []))
    credit_up = falling(list(reversed(fred.get("credit", []))))  # spreads rising
    vvix_hot = bool(yf.get("vvix")) and yf["vvix"][-1] > 110

    metric = 1.0
    triad = sum([stocks_down, bonds_down, gold_down])
    if triad >= 2:
        metric = 2.0
    if triad == 3:
        metric = 3.0
    if metric < 3.0 and (credit_up and vvix_hot):
        metric = 2.0
    return {"metric": metric, "value": triad, "series": [],
            "trend": f"{triad}/3 assets falling",
            "stocks_down": stocks_down, "bonds_down": bonds_down, "gold_down": gold_down}


async def _fetch_ofr() -> list[float]:
    """OFR Financial Stress Index daily CSV. Returns [] on any failure."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(OFR_FSI_CSV)
            resp.raise_for_status()
        vals: list[float] = []
        for line in resp.text.splitlines()[1:]:
            parts = line.split(",")
            try:
                vals.append(float(parts[-1]))
            except (ValueError, IndexError):
                continue
        return vals[-45:]
    except Exception as exc:  # noqa: BLE001
        log.warning("OFR FSI fetch failed (%s)", exc)
        return []
```

> **Note for implementer:** the OFR CSV column layout may need adjustment — confirm the real header with a quick `curl` and tweak `_fetch_ofr`. If the feed is unreliable, leaving it returning `[]` is acceptable (the indicator degrades to "n/a" and drops from the score). Same for `^VIX9D`/`^VVIX`/`^SKEW` — if Yahoo returns empty for any, the card shows "n/a" by design.

**Step 4: Run helper tests** — `cd backend && pytest tests/test_market_metrics.py -v` → Expected: PASS (4 tests)

**Step 5: Commit** — `feat(market): indicator assembly + stress-metric normalization`

---

## Phase 3 — Persistence + API (backend)

### Task 7: Snapshot + settings tables

**Files:**
- Modify: `backend/app/models.py` (append two models)
- Modify: `backend/app/database.py` (seed settings row)

**Step 1: Add models** to `backend/app/models.py`:

```python
class MarketSnapshot(Base):
    __tablename__ = "market_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pulled_at: Mapped[datetime | None] = mapped_column(DateTime)
    payload: Mapped[str | None] = mapped_column(Text)   # JSON: indicators + score


class MarketSettings(Base):
    __tablename__ = "market_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    payload: Mapped[str | None] = mapped_column(Text)   # JSON: thresholds + rules
```

**Step 2: Seed settings** in `backend/app/database.py` — import and seed:

```python
# add to imports
import json
from app.config import DEFAULT_WEATHER_SETTINGS
from app.models import Base, Assumption, MarketSettings

# add call inside init_db() after _seed_assumptions()
    _seed_market_settings()

# add function
def _seed_market_settings() -> None:
    with SessionLocal() as db:
        if db.get(MarketSettings, 1) is None:
            db.add(MarketSettings(id=1, payload=json.dumps(DEFAULT_WEATHER_SETTINGS)))
            db.commit()
```

**Step 3: Verify schema creates** — `cd backend && python -c "from app.database import init_db; init_db(); print('ok')"`
Expected: `ok`

**Step 4: Commit** — `feat(market): snapshot + settings tables with seed`

---

### Task 8: Market router (dashboard / refresh / settings)

**Files:**
- Create: `backend/app/routers/market.py`
- Modify: `backend/app/main.py` (register router)

**Step 1: Implement router**

Create `backend/app/routers/market.py`:

```python
"""Market Weathercast — cached dashboard, refresh, and adjustable settings."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import DEFAULT_WEATHER_SETTINGS, MARKET_STALE_SECONDS
from app.database import get_db
from app.models import MarketSnapshot, MarketSettings
from app.services import weather
from app.services.market_service import assemble_indicators

router = APIRouter(prefix="/api/market", tags=["market"])


def _settings(db: Session) -> dict:
    row = db.get(MarketSettings, 1)
    return json.loads(row.payload) if row and row.payload else DEFAULT_WEATHER_SETTINGS


def _latest(db: Session) -> MarketSnapshot | None:
    return db.query(MarketSnapshot).order_by(desc(MarketSnapshot.id)).first()


def _is_stale(snap: MarketSnapshot | None) -> bool:
    if snap is None or snap.pulled_at is None:
        return True
    age = (datetime.utcnow() - snap.pulled_at).total_seconds()
    return age > MARKET_STALE_SECONDS


def _build(indicators: dict, settings: dict, pulled_at: datetime) -> dict:
    result = weather.score(indicators, settings)
    return {
        "pulled_at": pulled_at.replace(tzinfo=timezone.utc).isoformat(),
        "indicators": indicators,
        "score": result,
        "thresholds": settings["thresholds"],
    }


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    snap = _latest(db)
    if snap is None:
        return {"stale": True, "payload": None}
    return {"stale": _is_stale(snap), "payload": json.loads(snap.payload)}


@router.post("/refresh")
async def refresh(db: Session = Depends(get_db)):
    indicators = await assemble_indicators()
    now = datetime.utcnow()
    payload = _build(indicators, _settings(db), now)
    db.add(MarketSnapshot(pulled_at=now, payload=json.dumps(payload)))
    # keep only the most recent 50 snapshots
    old = db.query(MarketSnapshot).order_by(desc(MarketSnapshot.id)).offset(50).all()
    for row in old:
        db.delete(row)
    db.commit()
    return {"stale": False, "payload": payload}


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    return _settings(db)


class SettingsIn(BaseModel):
    thresholds: dict
    rules: dict


@router.put("/settings")
def update_settings(body: SettingsIn, db: Session = Depends(get_db)):
    row = db.get(MarketSettings, 1)
    row.payload = json.dumps(body.model_dump())
    row.updated_at = datetime.utcnow()
    db.commit()
    # recompute the latest snapshot against new settings (no re-pull)
    snap = _latest(db)
    if snap and snap.payload:
        payload = json.loads(snap.payload)
        payload["score"] = weather.score(payload["indicators"], body.model_dump())
        payload["thresholds"] = body.thresholds
        snap.payload = json.dumps(payload)
        db.commit()
    return body.model_dump()


@router.post("/settings/reset")
def reset_settings(db: Session = Depends(get_db)):
    row = db.get(MarketSettings, 1)
    row.payload = json.dumps(DEFAULT_WEATHER_SETTINGS)
    row.updated_at = datetime.utcnow()
    db.commit()
    return DEFAULT_WEATHER_SETTINGS
```

**Step 2: Register** in `backend/app/main.py` — add `market` to the import and `app.include_router(market.router)`.

**Step 3: Verify it boots + endpoints exist**

Run: `cd backend && python -c "from app.main import app; print([r.path for r in app.routes if '/api/market' in r.path])"`
Expected: the 5 market paths printed.

**Step 4: Manual smoke** — start backend, then:
`curl -s http://localhost:9000/api/market/dashboard` → `{"stale": true, "payload": null}` initially.
`curl -s -X POST http://localhost:9000/api/market/refresh` → JSON with `score.level` 1–5.

**Step 5: Commit** — `feat(market): dashboard/refresh/settings API`

---

## Phase 4 — Frontend tabs refactor

### Task 9: Extract the screener into a tab, add the tab shell

**Files:**
- Create: `frontend/src/components/ScreenerView.tsx` (move current screener body here)
- Modify: `frontend/src/App.tsx`

**Step 1:** Move everything currently rendered inside `<Content>` (the `ScreenerFilters` + `ScreenerTable` + `AssumptionsDrawer` and their state/hooks) out of `App.tsx` into a new `ScreenerView.tsx` component that takes the props it needs (or owns its own `useScreener`/meta state — simplest is to relocate the existing hook calls into `ScreenerView`). Keep behavior identical.

**Step 2:** In `App.tsx`, render an Ant Design `<Tabs>` inside `<Content>`:

```tsx
import { Tabs } from "antd";
import ScreenerView from "./components/ScreenerView";
import Weathercast from "./components/market/Weathercast";

// inside <Content>:
<Tabs
  defaultActiveKey="screener"
  items={[
    { key: "screener", label: "Value Screener", children: <ScreenerView /> },
    { key: "weather", label: "Market Weathercast", children: <Weathercast /> },
  ]}
/>
```

> Keep the `AppHeader` (Pull Data / Assumptions) in the layout header. If those controls are screener-specific, that's fine for v1 — they simply don't affect the weather tab.

**Step 3: Verify** — `cd frontend && npm run dev`, open the app, confirm both tabs render and the screener still works exactly as before (filter, sort, open a row). Build a temporary placeholder `Weathercast` returning `<div>coming soon</div>` so the app compiles before Phase 6.

**Step 4: Commit** — `refactor(frontend): wrap screener in tabs, add weather tab shell`

---

## Phase 5 — Frontend types, API, hook

### Task 10: Types + API client + data hook

**Files:**
- Modify: `frontend/src/lib/types.ts` (append weather types)
- Modify: `frontend/src/lib/api.ts` (append market methods)
- Create: `frontend/src/hooks/useWeather.ts`

**Step 1: Add types** to `frontend/src/lib/types.ts`:

```ts
export interface Indicator {
  metric: number | null;
  value: number | null;
  series: number[];
  trend: string;
}
export interface ThresholdCfg {
  label: string; weight: number; green_max: number; yellow_max: number; unit: string;
}
export interface WeatherScore {
  level: number; weather: string; icon: string; base: number;
  states: Record<string, number | null>;
  fired_rules: string[]; missing: string[]; read: string;
}
export interface DashboardPayload {
  pulled_at: string;
  indicators: Record<string, Indicator>;
  score: WeatherScore;
  thresholds: Record<string, ThresholdCfg>;
}
export interface DashboardResponse { stale: boolean; payload: DashboardPayload | null; }
export interface WeatherSettings {
  thresholds: Record<string, ThresholdCfg>;
  rules: Record<string, boolean>;
}
```

**Step 2: Add API methods** to `frontend/src/lib/api.ts` (inside the `api` object):

```ts
  async marketDashboard(): Promise<DashboardResponse> {
    const { data } = await http.get<DashboardResponse>("/market/dashboard");
    return data;
  },
  async marketRefresh(): Promise<DashboardResponse> {
    const { data } = await http.post<DashboardResponse>("/market/refresh");
    return data;
  },
  async getWeatherSettings(): Promise<WeatherSettings> {
    const { data } = await http.get<WeatherSettings>("/market/settings");
    return data;
  },
  async updateWeatherSettings(body: WeatherSettings): Promise<WeatherSettings> {
    const { data } = await http.put<WeatherSettings>("/market/settings", body);
    return data;
  },
  async resetWeatherSettings(): Promise<WeatherSettings> {
    const { data } = await http.post<WeatherSettings>("/market/settings/reset");
    return data;
  },
```

(Add the new type names to the existing `import type { ... } from "./types";` line.)

**Step 3: Create hook** `frontend/src/hooks/useWeather.ts`:

```ts
import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { DashboardPayload } from "../lib/types";

export function useWeather() {
  const [payload, setPayload] = useState<DashboardPayload | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.marketRefresh();
      setPayload(res.payload);
    } finally {
      setLoading(false);
    }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.marketDashboard();
      if (res.payload && !res.stale) setPayload(res.payload);
      else await refresh(); // empty or stale -> auto-pull on tab open
    } finally {
      setLoading(false);
    }
  }, [refresh]);

  useEffect(() => { load(); }, [load]);
  return { payload, loading, refresh, setPayload };
}
```

**Step 4: Verify** types compile — `cd frontend && npx tsc --noEmit` → Expected: no errors.

**Step 5: Commit** — `feat(frontend): weather types, api client, data hook`

---

## Phase 6 — Frontend dashboard components

### Task 11: Sparkline (zero-dependency inline SVG)

**Files:**
- Create: `frontend/src/components/market/Sparkline.tsx`

**Step 1: Implement**

```tsx
interface Props { series: number[]; greenMax: number; yellowMax: number; width?: number; height?: number; }

export default function Sparkline({ series, greenMax, yellowMax, width = 140, height = 36 }: Props) {
  if (!series || series.length < 2) return <div style={{ height, opacity: 0.4 }}>n/a</div>;
  const min = Math.min(...series, greenMax);
  const max = Math.max(...series, yellowMax);
  const span = max - min || 1;
  const x = (i: number) => (i / (series.length - 1)) * width;
  const y = (v: number) => height - ((v - min) / span) * height;
  const path = series.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const last = series[series.length - 1];
  const stroke = last > yellowMax ? "#f87171" : last > greenMax ? "#fbbf24" : "#34d399";
  return (
    <svg width={width} height={height}>
      {/* threshold bands */}
      <rect x={0} y={0} width={width} height={y(yellowMax)} fill="#f87171" opacity={0.06} />
      <rect x={0} y={y(yellowMax)} width={width} height={y(greenMax) - y(yellowMax)} fill="#fbbf24" opacity={0.06} />
      <path d={path} fill="none" stroke={stroke} strokeWidth={1.5} />
    </svg>
  );
}
```

**Step 2: Commit** — `feat(frontend): inline SVG sparkline with threshold bands`

---

### Task 12: Indicator card + weather hero

**Files:**
- Create: `frontend/src/components/market/IndicatorCard.tsx`
- Create: `frontend/src/components/market/WeatherHero.tsx`

**Step 1: `IndicatorCard.tsx`**

```tsx
import { Card, Tag } from "antd";
import Sparkline from "./Sparkline";
import type { Indicator, ThresholdCfg } from "../../lib/types";

const PILL: Record<number, { color: string; text: string }> = {
  1: { color: "success", text: "Healthy" },
  2: { color: "warning", text: "Watch" },
  3: { color: "error", text: "Chaos" },
};

export default function IndicatorCard({ k, ind, cfg, state }:
  { k: string; ind: Indicator; cfg: ThresholdCfg; state: number | null }) {
  const pill = state ? PILL[state] : { color: "default", text: "n/a" };
  return (
    <Card size="small" title={cfg.label} extra={<Tag color={pill.color}>{pill.text}</Tag>}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 600 }}>
            {ind.value != null ? ind.value : "—"}{cfg.unit}
          </div>
          <div style={{ fontSize: 12, opacity: 0.7 }}>{ind.trend}</div>
        </div>
        <Sparkline series={ind.series} greenMax={cfg.green_max} yellowMax={cfg.yellow_max} />
      </div>
    </Card>
  );
}
```

**Step 2: `WeatherHero.tsx`**

```tsx
import { Button, Space } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import type { WeatherScore } from "../../lib/types";

const BG: Record<number, string> = {
  1: "#0f2a1f", 2: "#1f2a0f", 3: "#2a230f", 4: "#2a160f", 5: "#2a0f1a",
};

export default function WeatherHero({ score, pulledAt, loading, onRefresh }:
  { score: WeatherScore; pulledAt: string; loading: boolean; onRefresh: () => void }) {
  return (
    <div style={{ background: BG[score.level], borderRadius: 8, padding: "20px 24px", marginBottom: 16 }}>
      <Space size="large" align="center" style={{ justifyContent: "space-between", width: "100%" }}>
        <Space size="large" align="center">
          <span style={{ fontSize: 48 }}>{score.icon}</span>
          <div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{score.weather} · Concern {score.level}/5</div>
            <div style={{ opacity: 0.85 }}>{score.read}</div>
          </div>
        </Space>
        <Space direction="vertical" align="end">
          <Button icon={<ReloadOutlined />} loading={loading} onClick={onRefresh}>Refresh</Button>
          <span style={{ fontSize: 11, opacity: 0.6 }}>
            Updated {new Date(pulledAt).toLocaleString()}
          </span>
        </Space>
      </Space>
    </div>
  );
}
```

**Step 3: Commit** — `feat(frontend): indicator card + weather hero`

---

### Task 13: Weathercast container (replace placeholder)

**Files:**
- Create/replace: `frontend/src/components/market/Weathercast.tsx`

**Step 1: Implement**

```tsx
import { useState } from "react";
import { Row, Col, Spin, Empty, Button } from "antd";
import { SettingOutlined } from "@ant-design/icons";
import { useWeather } from "../../hooks/useWeather";
import WeatherHero from "./WeatherHero";
import IndicatorCard from "./IndicatorCard";
import WeatherSettingsDrawer from "./WeatherSettingsDrawer";

export default function Weathercast() {
  const { payload, loading, refresh, setPayload } = useWeather();
  const [settingsOpen, setSettingsOpen] = useState(false);

  if (!payload) return <div style={{ textAlign: "center", padding: 80 }}><Spin /></div>;

  const order = Object.entries(payload.thresholds)
    .sort((a, b) => b[1].weight - a[1].weight)
    .map(([k]) => k);

  return (
    <div>
      <WeatherHero score={payload.score} pulledAt={payload.pulled_at}
        loading={loading} onRefresh={refresh} />
      <div style={{ textAlign: "right", marginBottom: 12 }}>
        <Button icon={<SettingOutlined />} onClick={() => setSettingsOpen(true)}>Adjust ranges</Button>
      </div>
      <Row gutter={[12, 12]}>
        {order.map((k) => payload.indicators[k] && (
          <Col xs={24} sm={12} md={8} lg={6} key={k}>
            <IndicatorCard k={k} ind={payload.indicators[k]}
              cfg={payload.thresholds[k]} state={payload.score.states[k]} />
          </Col>
        ))}
      </Row>
      <WeatherSettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)}
        onSaved={refresh} />
    </div>
  );
}
```

**Step 2: Verify end-to-end** — run the app, open the Weathercast tab. Confirm: spinner → hero with a weather state + 1–5 → indicator cards with values, pills, and sparklines. Click **Refresh** and confirm the updated timestamp changes. Check the browser console + `/api/market/refresh` network call for errors.

**Step 3: Commit** — `feat(frontend): weathercast dashboard container`

---

## Phase 7 — Settings drawer (adjustable + reset)

### Task 14: Weather settings drawer

**Files:**
- Create: `frontend/src/components/market/WeatherSettingsDrawer.tsx`

**Step 1: Implement** (mirror `AssumptionsDrawer.tsx` structure: Drawer + form + Save/Reset). Load settings on open, render a numeric input pair (`green_max`, `yellow_max`) and a `weight` input per indicator, plus a switch per divergence rule. Save via `api.updateWeatherSettings`; Reset via `api.resetWeatherSettings`. On either, call `onSaved()` so the dashboard re-pulls/recomputes.

```tsx
import { useEffect, useState } from "react";
import { Drawer, Form, InputNumber, Switch, Button, Space, Divider, Typography } from "antd";
import { api } from "../../lib/api";
import type { WeatherSettings } from "../../lib/types";

export default function WeatherSettingsDrawer({ open, onClose, onSaved }:
  { open: boolean; onClose: () => void; onSaved: () => void }) {
  const [settings, setSettings] = useState<WeatherSettings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => { if (open) api.getWeatherSettings().then(setSettings); }, [open]);

  const patchThr = (k: string, field: string, v: number | null) =>
    setSettings((s) => s && ({ ...s, thresholds: { ...s.thresholds,
      [k]: { ...s.thresholds[k], [field]: v ?? 0 } } }));
  const patchRule = (k: string, v: boolean) =>
    setSettings((s) => s && ({ ...s, rules: { ...s.rules, [k]: v } }));

  const save = async () => {
    if (!settings) return;
    setSaving(true);
    try { await api.updateWeatherSettings(settings); onSaved(); onClose(); }
    finally { setSaving(false); }
  };
  const reset = async () => { const d = await api.resetWeatherSettings(); setSettings(d); onSaved(); };

  return (
    <Drawer title="Adjust indicator ranges" open={open} onClose={onClose} width={460}
      extra={<Space><Button onClick={reset}>Reset defaults</Button>
        <Button type="primary" loading={saving} onClick={save}>Save</Button></Space>}>
      {settings && (
        <Form layout="vertical">
          {Object.entries(settings.thresholds).map(([k, cfg]) => (
            <div key={k}>
              <Typography.Text strong>{cfg.label}</Typography.Text>
              <Space>
                <Form.Item label="Green ≤"><InputNumber value={cfg.green_max}
                  onChange={(v) => patchThr(k, "green_max", v)} /></Form.Item>
                <Form.Item label="Yellow ≤"><InputNumber value={cfg.yellow_max}
                  onChange={(v) => patchThr(k, "yellow_max", v)} /></Form.Item>
                <Form.Item label="Weight"><InputNumber min={0} value={cfg.weight}
                  onChange={(v) => patchThr(k, "weight", v)} /></Form.Item>
              </Space>
            </div>
          ))}
          <Divider>Divergence rules</Divider>
          {Object.entries(settings.rules).map(([k, on]) => (
            <Form.Item key={k} label={k}>
              <Switch checked={on} onChange={(v) => patchRule(k, v)} />
            </Form.Item>
          ))}
        </Form>
      )}
    </Drawer>
  );
}
```

**Step 2: Verify** — open drawer, change VIX `yellow_max` to a low number, Save, confirm VIX card flips to red and the hero level reacts. Click **Reset defaults**, confirm thresholds restore.

**Step 3: Commit** — `feat(frontend): adjustable + resettable weather settings drawer`

---

## Phase 8 — Integration & ship

### Task 15: Full verification pass

**Step 1:** `cd backend && pytest -v` — all engine + metric tests green (existing valuation tests still pass).
**Step 2:** `cd frontend && npx tsc --noEmit && npm run build` — clean build.
**Step 3:** `docker compose -f docker-compose.yml -f docker-compose.dev-ports.yml up --build` — open :3002, exercise both tabs:
  - Screener unchanged and working.
  - Weather tab auto-pulls on open, shows hero + cards, Refresh works, Adjust ranges saves + resets.
**Step 4:** Confirm graceful degradation — temporarily break one symbol (e.g. set a bad FRED id) and verify that card shows "n/a", drops from the score, and nothing 500s.

**Step 5: Commit** — `chore: market weathercast integration verified`

> **Optional follow-up (separate task, not v1):** the docker-export build for testers via the `anthropic-skills:docker-export` skill, per the existing test-build pattern (ports 3002/9000, output to `G:\Test_Builds\Stock_Screener`).

---

## Risks / things to watch

- **Yahoo symbol availability:** `^VVIX`, `^SKEW`, `^VIX9D` occasionally return empty from yfinance. Design already degrades to "n/a" — acceptable for v1. If chronic, swap SKEW/VVIX to CBOE CSV later.
- **OFR FSI CSV format:** confirm the real column layout before trusting `_fetch_ofr`; leave it returning `[]` if unreliable.
- **Net Liquidity scaling:** `net_liquidity_metric` uses a rough normalization; tune `green_max`/`yellow_max` against a real pull so green/yellow/red land sensibly.
- **Threshold direction:** every metric must be "higher = worse" before it reaches `weather.py`. NFCI and OFR FSI are already directionally correct (higher = more stress); Net Liquidity is inverted in the service.
```
