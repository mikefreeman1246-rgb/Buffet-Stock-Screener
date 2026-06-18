"""Data-pull pipeline control."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PullStatus
from app.services import pipeline_service
from app.utils import iso_utc

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/start")
async def start(limit: int | None = None, universe: str = "sp500"):
    if pipeline_service.is_running():
        return {"status": "already_running"}
    asyncio.create_task(pipeline_service.run_pull(limit=limit, universe=universe))
    return {"status": "started", "limit": limit, "universe": universe}


@router.post("/stop")
async def stop():
    pipeline_service.request_stop()
    return {"status": "stopping"}


@router.get("/status")
def status(db: Session = Depends(get_db)):
    last = db.query(PullStatus).order_by(PullStatus.id.desc()).first()
    return {
        "is_running": pipeline_service.is_running(),
        "last": None if last is None else {
            "status": last.status, "total": last.total, "completed": last.completed,
            "failed": last.failed, "last_ticker": last.last_ticker,
            "started_at": iso_utc(last.started_at),
            "completed_at": iso_utc(last.completed_at),
        },
    }
