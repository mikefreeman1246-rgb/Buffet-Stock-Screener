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
    if row is None:
        row = MarketSettings(id=1)
        db.add(row)
    row.payload = json.dumps(body.model_dump())
    row.updated_at = datetime.utcnow()
    db.commit()
    # recompute the latest snapshot against new settings (no re-pull)
    snap = _latest(db)
    if snap and snap.payload:
        payload = json.loads(snap.payload)
        if isinstance(payload, dict) and "indicators" in payload:
            payload["score"] = weather.score(payload["indicators"], body.model_dump())
            payload["thresholds"] = body.thresholds
            snap.payload = json.dumps(payload)
            db.commit()
    return body.model_dump()


@router.post("/settings/reset")
def reset_settings(db: Session = Depends(get_db)):
    row = db.get(MarketSettings, 1)
    if row is None:
        row = MarketSettings(id=1)
        db.add(row)
    row.payload = json.dumps(DEFAULT_WEATHER_SETTINGS)
    row.updated_at = datetime.utcnow()
    db.commit()
    return DEFAULT_WEATHER_SETTINGS
