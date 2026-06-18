"""Global valuation assumptions — get / update, plus live AAA-yield refresh."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assumption
from app.services.fred_service import fetch_aaa_yield

router = APIRouter(prefix="/api/assumptions", tags=["assumptions"])


class AssumptionsIn(BaseModel):
    aaa_bond_yield: float | None = None
    graham_base_pe: float | None = None
    graham_growth_multiplier: float | None = None
    graham_g_cap: float | None = None
    margin_of_safety_pct: float | None = None
    r_wide: float | None = None
    r_moderate: float | None = None
    r_narrow: float | None = None
    r_none: float | None = None
    terminal_growth: float | None = None
    high_growth_years: int | None = None


def _serialize(a: Assumption) -> dict:
    return {c.name: getattr(a, c.name) for c in Assumption.__table__.columns}


@router.get("")
def get_assumptions(db: Session = Depends(get_db)):
    return _serialize(db.get(Assumption, 1))


@router.put("")
def update_assumptions(body: AssumptionsIn, db: Session = Depends(get_db)):
    a = db.get(Assumption, 1)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(a, k, v)
    db.commit()
    return _serialize(a)


@router.post("/refresh-yield")
async def refresh_yield(db: Session = Depends(get_db)):
    """Pull the latest AAA yield from FRED and store it as Graham's Y."""
    y = await fetch_aaa_yield()
    a = db.get(Assumption, 1)
    a.aaa_bond_yield = y
    db.commit()
    return {"aaa_bond_yield": y}
