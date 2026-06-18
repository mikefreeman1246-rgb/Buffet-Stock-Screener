"""Data pull pipeline: seed S&P 500 -> yfinance -> SQLite, with WS progress.

yfinance is blocking, so each ticker fetch runs in a thread-pool executor with
bounded concurrency. Progress + failures are pushed over the WebSocket and
checkpointed in pull_status so the Header can render a live progress bar.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

from app.config import SEED_FILES, DEFAULT_UNIVERSE
from app.database import SessionLocal
from app.models import Stock, PullStatus
from app.services.yfinance_service import fetch_fundamentals
from app.websocket import manager

log = logging.getLogger(__name__)

# Yahoo throttles on burst volume (no API key). Keep concurrency modest and
# retry throttled tickers with backoff so large pulls (S&P 1500) self-heal
# instead of dropping ~2/3 of tickers when the rate limit trips.
CONCURRENCY = 4
MAX_ATTEMPTS = 4
BACKOFF_SECONDS = [2, 5, 12]  # waits between attempts (rate limits clear quickly)

_state = {"running": False, "stop": False}


def _is_rate_limited(exc: Exception) -> bool:
    s = str(exc).lower()
    return "429" in s or "too many requests" in s or "rate limit" in s


def load_seed(universe: str = DEFAULT_UNIVERSE) -> list[dict]:
    path = SEED_FILES.get(universe, SEED_FILES[DEFAULT_UNIVERSE])
    with open(path) as f:
        return json.load(f)


def is_running() -> bool:
    return _state["running"]


def request_stop() -> None:
    _state["stop"] = True


async def _broadcast(payload: dict) -> None:
    try:
        await manager.broadcast(payload)
    except Exception:  # noqa: BLE001
        pass


def _upsert(row: dict) -> None:
    with SessionLocal() as db:
        obj = db.get(Stock, row["ticker"])
        row = {**row, "updated_at": datetime.utcnow()}
        if obj is None:
            db.add(Stock(**row))
        else:
            for k, v in row.items():
                setattr(obj, k, v)
        db.commit()


async def _fetch_with_retry(loop, entry: dict) -> dict:
    """Fetch one ticker, retrying with backoff when Yahoo throttles us."""
    ticker = entry["ticker"]
    last_exc: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        if _state["stop"]:
            raise RuntimeError("stopped")
        try:
            return await loop.run_in_executor(
                None, fetch_fundamentals, ticker, entry.get("company", ""), entry.get("sector", "")
            )
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt == MAX_ATTEMPTS - 1:
                break
            wait = BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)]
            if _is_rate_limited(exc):
                wait *= 2  # back off harder on an explicit 429
            await asyncio.sleep(wait)
    assert last_exc is not None
    raise last_exc


async def run_pull(limit: int | None = None, universe: str = DEFAULT_UNIVERSE) -> None:
    """Pull fundamentals for the seed universe. Idempotent upsert."""
    if _state["running"]:
        return
    _state.update(running=True, stop=False)

    seed = load_seed(universe)
    if limit:
        seed = seed[:limit]
    total = len(seed)

    # status row
    with SessionLocal() as db:
        status = PullStatus(status="running", total=total, completed=0, failed=0,
                            started_at=datetime.utcnow())
        db.add(status)
        db.commit()
        status_id = status.id

    completed = failed = 0
    sem = asyncio.Semaphore(CONCURRENCY)
    loop = asyncio.get_running_loop()

    async def worker(entry: dict) -> None:
        nonlocal completed, failed
        if _state["stop"]:
            return
        async with sem:
            ticker = entry["ticker"]
            try:
                data = await _fetch_with_retry(loop, entry)
                _upsert(data)
            except Exception as exc:  # noqa: BLE001
                failed += 1
                log.warning("pull failed for %s after retries: %s", ticker, exc)
            finally:
                completed += 1
                if completed % 5 == 0 or completed == total:
                    _checkpoint(status_id, completed, failed, ticker)
                await _broadcast({
                    "type": "progress", "phase": "fundamentals",
                    "completed": completed, "total": total,
                    "failed": failed, "ticker": ticker,
                })

    await asyncio.gather(*(worker(e) for e in seed))

    final = "completed" if not _state["stop"] else "paused"
    _checkpoint(status_id, completed, failed, None, final)
    await _broadcast({"type": "done", "status": final, "completed": completed,
                      "total": total, "failed": failed, "universe": universe})
    _state["running"] = False


def _checkpoint(status_id: int, completed: int, failed: int,
                ticker: str | None, status: str | None = None) -> None:
    with SessionLocal() as db:
        row = db.get(PullStatus, status_id)
        if row is None:
            return
        row.completed = completed
        row.failed = failed
        if ticker:
            row.last_ticker = ticker
        if status:
            row.status = status
            row.completed_at = datetime.utcnow()
        db.commit()
