"""Main screener endpoint — computes both models live and filters/sorts/paginates."""
from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Stock, Override, Assumption, StockTag
from app.services.compute import assumptions_from_row, evaluate_row

router = APIRouter(prefix="/api", tags=["screener"])

# Rank maps so categorical columns sort by quality/bullishness, not alphabetically.
# Higher rank = better/more bullish, so a "desc" sort surfaces the best first.
MOAT_RANK = {"wide": 4, "moderate": 3, "narrow": 2, "none": 1}
GRAHAM_RANK = {"Undervalued": 4, "Fair Value": 3, "Mild Overvalued": 2, "Overvalued": 1, "N/A": 0}
BUFFETT_RANK = {"Strong Buy": 5, "Buy": 4, "Hold": 3, "Trim": 2, "Pass": 1, "N/A": 0}
CONVICTION_RANK = {"Max Conviction": 5, "Moat Premium": 4, "Mixed": 3, "Value Trap?": 2, "Avoid": 1}
RANK_MAPS = {
    "moat": MOAT_RANK,
    "graham_verdict": GRAHAM_RANK,
    "buffett_verdict": BUFFETT_RANK,
    "conviction": CONVICTION_RANK,
}

# assumption fields that may be overridden per-request for live what-if
_ASSUMPTION_PARAMS = {
    "aaa_bond_yield", "graham_base_pe", "graham_growth_multiplier", "graham_g_cap",
    "margin_of_safety_pct", "r_wide", "r_moderate", "r_narrow", "r_none",
    "terminal_growth",
}


@router.get("/screener")
def screen(
    db: Session = Depends(get_db),
    model: str = Query("dual"),                       # graham|buffett|dual (controls columns)
    graham_verdict: list[str] | None = Query(None),
    buffett_verdict: list[str] | None = Query(None),
    moat: list[str] | None = Query(None),
    conviction: list[str] | None = Query(None),
    tags: list[str] | None = Query(None),          # match ANY of these tags
    sector: list[str] | None = Query(None),
    min_margin: float | None = Query(None),          # min margin-of-safety % for the model
    min_price: float | None = Query(None),
    max_price: float | None = Query(None),
    min_cap: float | None = Query(None),
    max_cap: float | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("market_cap"),
    sort_dir: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    # live assumption what-if (all optional)
    aaa_bond_yield: float | None = Query(None),
    graham_g_cap: float | None = Query(None),
    margin_of_safety_pct: float | None = Query(None),
    r_wide: float | None = Query(None),
    r_moderate: float | None = Query(None),
    r_narrow: float | None = Query(None),
    r_none: float | None = Query(None),
    terminal_growth: float | None = Query(None),
):
    a = assumptions_from_row(db.get(Assumption, 1))
    # merge live what-if overrides
    live = {k: v for k, v in {
        "aaa_bond_yield": aaa_bond_yield, "graham_g_cap": graham_g_cap,
        "margin_of_safety_pct": margin_of_safety_pct, "r_wide": r_wide,
        "r_moderate": r_moderate, "r_narrow": r_narrow, "r_none": r_none,
        "terminal_growth": terminal_growth,
    }.items() if v is not None}
    if live:
        a = replace(a, **live)

    overrides = {o.ticker: o for o in db.query(Override).all()}
    tag_map: dict[str, list[str]] = {}
    for t in db.query(StockTag).all():
        tag_map.setdefault(t.ticker, []).append(t.tag)
    stocks = db.query(Stock).all()
    rows = []
    for s in stocks:
        r = evaluate_row(s, a, overrides.get(s.ticker))
        r["tags"] = sorted(tag_map.get(s.ticker, []), key=str.lower)
        rows.append(r)

    margin_key = "buffett_margin_pct" if model == "buffett" else "graham_margin_pct"

    def keep(r: dict) -> bool:
        if sector and r["sector"] not in sector:
            return False
        if graham_verdict and r.get("graham_verdict") not in graham_verdict:
            return False
        if buffett_verdict and r.get("buffett_verdict") not in buffett_verdict:
            return False
        if moat and r.get("moat") not in moat:
            return False
        if conviction and r.get("conviction") not in conviction:
            return False
        if tags and not (set(r.get("tags", [])) & set(tags)):
            return False
        if min_margin is not None:
            m = r.get(margin_key)
            if m is None or m < min_margin:
                return False
        if min_price is not None and (r["price"] is None or r["price"] < min_price):
            return False
        if max_price is not None and (r["price"] is None or r["price"] > max_price):
            return False
        if min_cap is not None and (r["market_cap"] is None or r["market_cap"] < min_cap):
            return False
        if max_cap is not None and (r["market_cap"] is None or r["market_cap"] > max_cap):
            return False
        if search:
            q = search.lower()
            if q not in r["ticker"].lower() and q not in (r["company"] or "").lower():
                return False
        return True

    filtered = [r for r in rows if keep(r)]

    reverse = sort_dir == "desc"
    if sort_by in RANK_MAPS:
        rank = RANK_MAPS[sort_by]
        filtered.sort(key=lambda r: rank.get(r.get(sort_by), -1), reverse=reverse)
    elif sort_by == "tags":
        # group by joined tag string; untagged rows sort to the end either way
        filtered.sort(key=lambda r: (not r.get("tags"), ", ".join(r.get("tags", [])).lower()),
                      reverse=reverse)
    else:
        filtered.sort(key=lambda r: (r.get(sort_by) is None, r.get(sort_by) or 0), reverse=reverse)

    total = len(filtered)
    start = (page - 1) * page_size
    paged = filtered[start:start + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "assumptions": a.as_dict(),
        "results": paged,
    }
