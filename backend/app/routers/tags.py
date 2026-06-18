"""User-defined stock tags: list all, and set a stock's tag list."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Stock, StockTag

router = APIRouter(prefix="/api", tags=["tags"])


class TagsIn(BaseModel):
    tags: list[str]


def _clean(tags: list[str]) -> list[str]:
    """Trim, drop blanks, de-dupe (case-insensitive), preserve first-seen order."""
    seen: set[str] = set()
    out: list[str] = []
    for t in tags:
        t = t.strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out


@router.get("/tags")
def list_tags(db: Session = Depends(get_db)):
    """All distinct tags with how many stocks carry each (for the filter UI)."""
    rows = (
        db.query(StockTag.tag, func.count(StockTag.ticker))
        .group_by(StockTag.tag)
        .order_by(func.lower(StockTag.tag))
        .all()
    )
    return [{"tag": tag, "count": count} for tag, count in rows]


@router.put("/stocks/{ticker}/tags")
def set_tags(ticker: str, body: TagsIn, db: Session = Depends(get_db)):
    """Replace a stock's full tag set. Returns the cleaned list."""
    ticker = ticker.upper()
    if db.get(Stock, ticker) is None:
        raise HTTPException(404, f"{ticker} not found")
    db.query(StockTag).filter(StockTag.ticker == ticker).delete()
    tags = _clean(body.tags)
    for t in tags:
        db.add(StockTag(ticker=ticker, tag=t))
    db.commit()
    return {"ticker": ticker, "tags": tags}
