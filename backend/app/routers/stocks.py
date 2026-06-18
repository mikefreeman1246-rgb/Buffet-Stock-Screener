"""Per-stock detail (full valuation breakdown) and override management."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Stock, Override, Assumption, StockTag
from app.services.compute import assumptions_from_row, evaluate_row

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


class OverrideIn(BaseModel):
    growth_override: float | None = None
    moat_override: str | None = None
    oe_multiplier_override: float | None = None
    normalized_eps_override: float | None = None
    note: str | None = None


@router.get("/{ticker}")
def get_stock(ticker: str, db: Session = Depends(get_db)):
    s = db.get(Stock, ticker.upper())
    if s is None:
        raise HTTPException(404, f"{ticker} not found")
    a = assumptions_from_row(db.get(Assumption, 1))
    o = db.get(Override, ticker.upper())
    result = evaluate_row(s, a, o)
    result["tags"] = sorted(
        (t.tag for t in db.query(StockTag).filter(StockTag.ticker == ticker.upper()).all()),
        key=str.lower,
    )
    result["raw"] = {c.name: getattr(s, c.name) for c in Stock.__table__.columns}
    result["override"] = None if o is None else {
        "growth_override": o.growth_override, "moat_override": o.moat_override,
        "oe_multiplier_override": o.oe_multiplier_override,
        "normalized_eps_override": o.normalized_eps_override, "note": o.note,
    }
    return result


@router.put("/{ticker}/override")
def set_override(ticker: str, body: OverrideIn, db: Session = Depends(get_db)):
    ticker = ticker.upper()
    if db.get(Stock, ticker) is None:
        raise HTTPException(404, f"{ticker} not found")
    o = db.get(Override, ticker)
    data = body.model_dump()
    if o is None:
        o = Override(ticker=ticker, **data, updated_at=datetime.utcnow())
        db.add(o)
    else:
        for k, v in data.items():
            setattr(o, k, v)
        o.updated_at = datetime.utcnow()
    db.commit()
    # recompute and return the fresh row
    a = assumptions_from_row(db.get(Assumption, 1))
    return evaluate_row(db.get(Stock, ticker), a, o)


@router.delete("/{ticker}/override")
def clear_override(ticker: str, db: Session = Depends(get_db)):
    o = db.get(Override, ticker.upper())
    if o is not None:
        db.delete(o)
        db.commit()
    return {"ok": True}
