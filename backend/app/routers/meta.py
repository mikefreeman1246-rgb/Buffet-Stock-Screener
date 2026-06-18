"""Snapshot metadata: freshness, counts, available sectors."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Stock, PullStatus
from app.utils import iso_utc

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    count = db.query(func.count(Stock.ticker)).scalar() or 0
    last_update = db.query(func.max(Stock.updated_at)).scalar()
    last_pull = db.query(PullStatus).order_by(PullStatus.id.desc()).first()
    sectors = [s[0] for s in db.query(Stock.sector).distinct().all() if s[0]]
    return {
        "stock_count": count,
        "last_update": iso_utc(last_update),
        "sectors": sorted(sectors),
        "last_pull_status": last_pull.status if last_pull else None,
    }
