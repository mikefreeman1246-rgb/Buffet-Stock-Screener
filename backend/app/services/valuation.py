"""Valuation engine — pure functions implementing the two formula docs.

Source of truth:
  - graham-valuation-formula.txt   (Graham intrinsic value + verdict bands)
  - buffett-modernized-formula.txt (Buffett 2-stage owner-earnings DCF,
    moat discount rates, owner earnings, financial P/B, verdict bands)

Nothing in this module performs I/O. Every function takes plain numbers (and an
Assumptions object) so it can be unit-tested directly against the worked
examples in the docs. `evaluate()` is the single entry point used by the API.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.config import Assumptions, FINANCIAL_SECTORS


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
@dataclass
class Fundamentals:
    """Raw per-stock inputs (a snapshot row from yfinance)."""
    ticker: str
    company: str = ""
    sector: str = ""
    price: Optional[float] = None
    eps_ttm: Optional[float] = None
    eps_growth: Optional[float] = None        # decimal fraction, e.g. 0.218 = 21.8%
    roe: Optional[float] = None               # decimal fraction
    book_value_ps: Optional[float] = None
    shares_out: Optional[float] = None
    net_income: Optional[float] = None
    dep_amort: Optional[float] = None
    capex: Optional[float] = None             # may be negative (cash outflow)
    free_cash_flow: Optional[float] = None
    gross_margin: Optional[float] = None      # decimal fraction (moat proxy)
    profit_margin: Optional[float] = None     # decimal fraction (moat proxy)


@dataclass
class Overrides:
    """Per-stock manual judgment; any None falls back to auto-derivation."""
    growth_override: Optional[float] = None        # percent (whole number)
    moat_override: Optional[str] = None            # wide|moderate|narrow|none
    oe_multiplier_override: Optional[float] = None  # OE = EPS * multiplier
    normalized_eps_override: Optional[float] = None  # replaces EPS base (cyclicals)


# --------------------------------------------------------------------------- #
# Helpers — input derivation
# --------------------------------------------------------------------------- #
def effective_eps(f: Fundamentals, ov: Overrides) -> Optional[float]:
    if ov.normalized_eps_override is not None:
        return ov.normalized_eps_override
    return f.eps_ttm


def effective_growth_pct(f: Fundamentals, ov: Overrides, g_cap: float) -> float:
    """Growth `g` as a whole-number percent, capped at the Graham ceiling."""
    if ov.growth_override is not None:
        g = ov.growth_override
    elif f.eps_growth is not None:
        g = f.eps_growth * 100.0
    else:
        g = 0.0
    return max(0.0, min(g, g_cap))


def classify_moat(f: Fundamentals, ov: Overrides) -> str:
    """Heuristic moat proxy from ROE + margins. Overridable per stock.

    This is an approximation, NOT a judgment call like the docs' hand-assigned
    moats. Clearly surfaced as a proxy in the UI.
    """
    if ov.moat_override is not None:
        return ov.moat_override
    roe = f.roe if f.roe is not None else 0.0
    # gross/profit margins are not always present; treat missing as 0.
    gm = getattr(f, "gross_margin", None) or 0.0
    pm = getattr(f, "profit_margin", None) or 0.0
    if roe > 0.20 and gm > 0.40 and pm > 0.15:
        return "wide"
    if roe > 0.15 and pm > 0.10:
        return "moderate"
    if roe > 0.08:
        return "narrow"
    return "none"


def owner_earnings_ps(f: Fundamentals, ov: Overrides, eps_base: Optional[float]):
    """Owner earnings per share + the implied multiplier vs EPS.

    Priority:
      1. explicit OE multiplier override -> OE = EPS * multiplier
      2. cash-flow derivation: (NI + D&A - maintenance capex) / shares
         maintenance capex approximated conservatively as min(|capex|, D&A)
      3. free cash flow / shares
    Returns (oe_ps, multiplier, method).
    """
    if ov.oe_multiplier_override is not None and eps_base is not None:
        return eps_base * ov.oe_multiplier_override, ov.oe_multiplier_override, "override"

    shares = f.shares_out
    if shares and f.net_income is not None and f.dep_amort is not None and f.capex is not None:
        maint_capex = min(abs(f.capex), f.dep_amort)
        oe_total = f.net_income + f.dep_amort - maint_capex
        oe_ps = oe_total / shares
        mult = (oe_ps / eps_base) if eps_base not in (None, 0) else None
        return oe_ps, mult, "cashflow"

    if shares and f.free_cash_flow is not None:
        oe_ps = f.free_cash_flow / shares
        mult = (oe_ps / eps_base) if eps_base not in (None, 0) else None
        return oe_ps, mult, "fcf"

    # last resort: fall back to EPS itself (OE multiplier 1.0)
    if eps_base is not None:
        return eps_base, 1.0, "eps_fallback"
    return None, None, "none"


# --------------------------------------------------------------------------- #
# Graham
# --------------------------------------------------------------------------- #
def graham_value(eps: float, g_pct: float, a: Assumptions) -> float:
    """V = EPS x (base_pe + growth_mult * g) x (4.4 / Y).  g is whole percent."""
    multiplier = a.graham_base_pe + a.graham_growth_multiplier * g_pct
    bond_adj = 4.4 / a.aaa_bond_yield
    return eps * multiplier * bond_adj


def graham_verdict(price: float, value: float) -> str:
    """Price vs Graham value bands (graham doc 'Verdict Thresholds')."""
    if value <= 0:
        return "N/A"
    ratio = price / value
    if ratio < 0.85:
        return "Undervalued"
    if ratio < 1.10:
        return "Fair Value"
    if ratio < 1.35:
        return "Mild Overvalued"
    return "Overvalued"


# --------------------------------------------------------------------------- #
# Buffett — two-stage owner-earnings DCF
# --------------------------------------------------------------------------- #
def buffett_value(oe: float, g_pct: float, r_pct: float, a: Assumptions) -> float:
    """Two-stage DCF. g, r, terminal growth are percents; converted internally."""
    g = g_pct / 100.0
    r = r_pct / 100.0
    tg = a.terminal_growth / 100.0
    n = a.high_growth_years

    # Stage 1 — high-growth period
    if abs(g - r) < 1e-9:
        s1 = n * oe / (1 + r)                          # L'Hopital limit
    else:
        s1 = oe * (1 - ((1 + g) / (1 + r)) ** n) / (r - g)

    # Stage 2 — terminal / perpetuity value
    terminal_oe = oe * (1 + g) ** n
    s2 = terminal_oe * (1 + tg) / ((r - tg) * (1 + r) ** n)
    return s1 + s2


def _moat_bonus(moat: str) -> float:
    return {"wide": 0.05, "moderate": 0.02}.get(moat, 0.0)


def buffett_verdict(value: float, price: float, moat: str) -> tuple[str, float]:
    """Returns (verdict, adjusted_ratio). ratio = value/price, moat-bonused."""
    if price <= 0 or value <= 0:
        return "N/A", 0.0
    ratio = (value / price) * (1 + _moat_bonus(moat))
    if ratio >= 1.50:
        v = "Strong Buy"
    elif ratio >= 1.20:
        v = "Buy"
    elif ratio >= 0.92:
        v = "Hold"
    elif ratio >= 0.78:
        v = "Trim"
    else:
        v = "Pass"
    return v, ratio


# --------------------------------------------------------------------------- #
# Financial companies — justified price-to-book (Buffett doc Mod #4)
# --------------------------------------------------------------------------- #
PB_SPREAD_FLOOR = 0.03   # sustainable growth must leave >=3% below r
PB_CEILING = 5.0         # clamp justified P/B to a sane range


def financial_pb_value(roe: float, g_pct: float, r_pct: float, book_ps: float):
    """fair_P/B = (ROE - g)/(r - g); V = fair_P/B * book value per share.

    `g` here is a *sustainable* long-run growth, not a short-term spike, so it is
    capped to leave at least a 3% spread below r (the Gordon model is singular as
    g -> r). The resulting P/B is clamped to a sane ceiling. Returns
    (value, fair_pb) or (None, None) if not computable.
    """
    if book_ps is None or book_ps <= 0 or roe is None:
        return None, None
    g = g_pct / 100.0
    r = r_pct / 100.0
    g = min(g, r - PB_SPREAD_FLOOR)   # keep a meaningful r - g spread
    if r - g <= 0:
        return None, None
    fair_pb = (roe - g) / (r - g)
    fair_pb = max(0.0, min(fair_pb, PB_CEILING))
    return fair_pb * book_ps, fair_pb


# --------------------------------------------------------------------------- #
# Dual conviction
# --------------------------------------------------------------------------- #
def dual_conviction(graham_v: str, buffett_v: str) -> str:
    graham_cheap = graham_v == "Undervalued"
    graham_rich = graham_v in ("Overvalued", "Mild Overvalued")
    buffett_buy = buffett_v in ("Strong Buy", "Buy")
    buffett_sell = buffett_v in ("Trim", "Pass")

    if graham_cheap and buffett_buy:
        return "Max Conviction"
    if graham_rich and buffett_sell:
        return "Avoid"
    if graham_rich and buffett_buy:
        return "Moat Premium"
    if graham_cheap and buffett_sell:
        return "Value Trap?"
    return "Mixed"


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def evaluate(f: Fundamentals, a: Assumptions, ov: Optional[Overrides] = None) -> dict:
    """Compute both models for one stock. Returns a flat dict for the API."""
    ov = ov or Overrides()
    is_financial = f.sector in FINANCIAL_SECTORS

    eps = effective_eps(f, ov)
    g_pct = effective_growth_pct(f, ov, a.graham_g_cap)
    moat = classify_moat(f, ov)
    r_pct = a.discount_rate(moat)
    price = f.price

    out: dict = {
        "ticker": f.ticker,
        "company": f.company,
        "sector": f.sector,
        "price": price,
        "is_financial": is_financial,
        "eps_used": eps,
        "growth_pct": g_pct,
        "moat": moat,
        "discount_rate": r_pct,
    }

    # --- Graham ---
    if eps is not None and eps > 0:
        gv = graham_value(eps, g_pct, a)
        out["graham_value"] = gv
        out["graham_sweet_spot"] = gv * (1 - a.margin_of_safety_pct)
        out["graham_verdict"] = graham_verdict(price, gv) if price else "N/A"
        out["graham_margin_pct"] = ((gv - price) / gv * 100.0) if (price and gv > 0) else None
    else:
        out["graham_value"] = None
        out["graham_sweet_spot"] = None
        out["graham_verdict"] = "N/A"
        out["graham_margin_pct"] = None

    # --- Buffett ---
    oe_ps, oe_mult, oe_method = owner_earnings_ps(f, ov, eps)
    out["owner_earnings_ps"] = oe_ps
    out["oe_multiplier"] = oe_mult
    out["oe_method"] = oe_method

    if is_financial:
        # Justified P/B is the Buffett-side value for banks/insurers.
        pb_val, fair_pb = financial_pb_value(f.roe, g_pct, r_pct, f.book_value_ps)
        out["buffett_method"] = "pb"
        out["fair_pb"] = fair_pb
        if pb_val is not None and pb_val > 0 and price:
            out["buffett_value"] = pb_val
            verdict, ratio = buffett_verdict(pb_val, price, moat)
            out["buffett_verdict"] = verdict
            out["buffett_ratio"] = ratio
            out["buffett_margin_pct"] = (pb_val - price) / pb_val * 100.0
        else:
            out["buffett_value"] = None
            out["buffett_verdict"] = "N/A"
            out["buffett_ratio"] = None
            out["buffett_margin_pct"] = None
    else:
        out["buffett_method"] = "dcf"
        out["fair_pb"] = None
        if oe_ps is not None and oe_ps > 0:
            bv = buffett_value(oe_ps, g_pct, r_pct, a)
            out["buffett_value"] = bv
            verdict, ratio = buffett_verdict(bv, price, moat) if price else ("N/A", None)
            out["buffett_verdict"] = verdict
            out["buffett_ratio"] = ratio
            out["buffett_margin_pct"] = ((bv - price) / bv * 100.0) if (price and bv > 0) else None
        else:
            out["buffett_value"] = None
            out["buffett_verdict"] = "N/A"
            out["buffett_ratio"] = None
            out["buffett_margin_pct"] = None

    out["conviction"] = dual_conviction(out["graham_verdict"], out["buffett_verdict"])
    return out
