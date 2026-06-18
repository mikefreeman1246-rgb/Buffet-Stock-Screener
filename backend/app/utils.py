"""Small shared helpers."""
from __future__ import annotations

from datetime import datetime, timezone


def iso_utc(dt: datetime | str | None) -> str | None:
    """Serialize a stored (naive UTC) datetime as a tz-aware ISO string.

    The pipeline writes timestamps with datetime.utcnow(), which are naive but
    represent UTC. Tagging them with the UTC offset lets the browser's
    `new Date()` convert to the user's local time instead of mistaking UTC for
    local. Strings (already serialized by SQLite) are passed through.
    """
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt if ("Z" in dt or "+" in dt) else dt + "+00:00"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
