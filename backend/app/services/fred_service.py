"""Fetch the AAA corporate bond yield (Graham's Y) from FRED — no API key.

FRED exposes a public CSV download for any series. We read DAAA (Moody's
Seasoned AAA Corporate Bond Yield) and take the most recent numeric value.
Falls back to the documented default if the network is unavailable.
"""
from __future__ import annotations

import csv
import io
import logging

import httpx

from app.config import FRED_AAA_CSV_URL, FRED_FALLBACK_YIELD

log = logging.getLogger(__name__)


async def fetch_aaa_yield() -> float:
    """Return the latest AAA yield as a percent (e.g. 5.56). Never raises."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(FRED_AAA_CSV_URL)
            resp.raise_for_status()
        return _parse_latest(resp.text)
    except Exception as exc:  # noqa: BLE001 — degrade gracefully
        log.warning("FRED AAA fetch failed (%s); using fallback %.2f", exc, FRED_FALLBACK_YIELD)
        return FRED_FALLBACK_YIELD


def _parse_latest(csv_text: str) -> float:
    """Parse FRED CSV; return the last row with a numeric value."""
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    if not rows:
        return FRED_FALLBACK_YIELD
    # header is like ["observation_date" or "DATE", "DAAA"]; value is last column
    latest = FRED_FALLBACK_YIELD
    for row in rows[1:]:
        if len(row) < 2:
            continue
        raw = row[-1].strip()
        if raw in ("", "."):  # FRED uses "." for missing observations
            continue
        try:
            latest = float(raw)
        except ValueError:
            continue
    return latest
