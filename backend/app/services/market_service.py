"""Pull all weather inputs, normalize to stress metrics, assemble indicators.

Every indicator dict has: metric (higher=worse, None if no data), value (raw,
for display), series (last ~14 points for the sparkline), trend (label string).
Cascade additionally carries stocks_down / bonds_down / gold_down booleans.
"""
from __future__ import annotations

import logging

import httpx

from app.config import MARKET_FRED_SERIES, MARKET_YF_SYMBOLS, OFR_FSI_CSV
from app.services.market_fred import fetch_series
from app.services.market_yf import fetch_closes

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


def net_liquidity_series(walcl: list[float], tga: list[float], rrp: list[float]) -> list[float]:
    """Net liquidity = Fed assets - TGA - RRP, in millions, oldest..newest.

    WALCL (Fed total assets) and WTREGEN (TGA) are both weekly H.4.1 series in
    millions and arrive date-aligned, so we subtract them element-wise on their
    common tail. RRP (RRPONTSYD) is a *daily* series in *billions*, so it can't
    be zipped by index; we convert its latest level to millions and subtract it
    as a (currently tiny) constant offset. It cancels out of any trend change.
    """
    n = min(len(walcl), len(tga))
    if n < 1:
        return []
    rrp_m = rrp[-1] * 1000.0 if rrp else 0.0  # billions -> millions, latest level
    return [walcl[-(n - i)] - tga[-(n - i)] - rrp_m for i in range(n)]


def net_liquidity_metric(walcl: list[float], tga: list[float], rrp: list[float]) -> float | None:
    """Stress metric = the % DRAIN in net liquidity over ~4 weeks (higher = more
    stress). Falling liquidity -> positive; rising/flat -> <=0."""
    nl = net_liquidity_series(walcl, tga, rrp)
    if len(nl) < 2:
        return None
    look = min(4, len(nl) - 1)  # weekly series -> ~4 weeks
    base = nl[-1 - look]
    if base == 0:
        return None
    pct = (nl[-1] - base) / base * 100.0
    return -pct  # drain (falling) -> positive stress


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
    nl_series = net_liquidity_series(fred["walcl"], fred["tga"], fred["rrp"])
    nl_metric = net_liquidity_metric(fred["walcl"], fred["tga"], fred["rrp"])
    ind["net_liquidity"] = card(
        nl_metric,
        round(nl_series[-1] / 1e6, 2) if nl_series else None,  # display level in $T
        [round(v / 1e6, 3) for v in nl_series],                # sparkline in $T
        (f"{-nl_metric:+.1f}% / 4wk" if nl_metric is not None else "n/a"))
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
    if not yf.get("spx") and not yf.get("tlt") and not yf.get("gold"):
        # Full feed outage: no data to judge, so exclude from the score like
        # every other indicator (metric=None) rather than fabricating green.
        return {"metric": None, "value": None, "series": [], "trend": "n/a",
                "stocks_down": False, "bonds_down": False, "gold_down": False}

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
