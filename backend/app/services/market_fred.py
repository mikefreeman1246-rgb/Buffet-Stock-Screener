"""Fetch recent history for arbitrary FRED series via public CSV (no API key)."""
from __future__ import annotations

import csv
import io
import logging

import httpx

from app.config import FRED_CSV

log = logging.getLogger(__name__)


async def fetch_series(series_id: str, days: int = 45) -> list[tuple[str, float]]:
    """Return [(date, value)] for the last ~`days` observations. Never raises."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(FRED_CSV.format(series=series_id))
            resp.raise_for_status()
        return _parse(resp.text)[-days:]
    except Exception as exc:  # noqa: BLE001 — degrade gracefully
        log.warning("FRED %s fetch failed (%s)", series_id, exc)
        return []


def _parse(csv_text: str) -> list[tuple[str, float]]:
    rows = list(csv.reader(io.StringIO(csv_text)))
    out: list[tuple[str, float]] = []
    for row in rows[1:]:
        if len(row) < 2:
            continue
        raw = row[-1].strip()
        if raw in ("", "."):
            continue
        try:
            out.append((row[0], float(raw)))
        except ValueError:
            continue
    return out
