"""Glue between ORM rows and the pure valuation engine."""
from __future__ import annotations

from app.config import Assumptions
from app.models import Stock, Override, Assumption
from app.services.valuation import Fundamentals, Overrides, evaluate


def assumptions_from_row(row: Assumption | None) -> Assumptions:
    if row is None:
        return Assumptions()
    return Assumptions(
        aaa_bond_yield=row.aaa_bond_yield,
        graham_base_pe=row.graham_base_pe,
        graham_growth_multiplier=row.graham_growth_multiplier,
        graham_g_cap=row.graham_g_cap,
        margin_of_safety_pct=row.margin_of_safety_pct,
        r_wide=row.r_wide,
        r_moderate=row.r_moderate,
        r_narrow=row.r_narrow,
        r_none=row.r_none,
        terminal_growth=row.terminal_growth,
        high_growth_years=row.high_growth_years,
    )


def fundamentals_from_row(s: Stock) -> Fundamentals:
    return Fundamentals(
        ticker=s.ticker, company=s.company or "", sector=s.sector or "",
        price=s.price, eps_ttm=s.eps_ttm, eps_growth=s.eps_growth, roe=s.roe,
        book_value_ps=s.book_value_ps, shares_out=s.shares_out,
        net_income=s.net_income, dep_amort=s.dep_amort, capex=s.capex,
        free_cash_flow=s.free_cash_flow, gross_margin=s.gross_margin,
        profit_margin=s.profit_margin,
    )


def overrides_from_row(o: Override | None) -> Overrides:
    if o is None:
        return Overrides()
    return Overrides(
        growth_override=o.growth_override,
        moat_override=o.moat_override,
        oe_multiplier_override=o.oe_multiplier_override,
        normalized_eps_override=o.normalized_eps_override,
    )


def evaluate_row(s: Stock, a: Assumptions, o: Override | None) -> dict:
    out = evaluate(fundamentals_from_row(s), a, overrides_from_row(o))
    out["market_cap"] = s.market_cap
    out["has_override"] = o is not None and any([
        o.growth_override is not None, o.moat_override is not None,
        o.oe_multiplier_override is not None, o.normalized_eps_override is not None,
    ])
    return out
