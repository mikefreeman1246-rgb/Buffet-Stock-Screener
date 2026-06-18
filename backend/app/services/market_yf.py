"""Fetch ~6 weeks of daily closes for market symbols via yfinance. Never raises."""
from __future__ import annotations

import logging

import yfinance as yf

log = logging.getLogger(__name__)


def fetch_closes(symbols: dict[str, str], period: str = "2mo") -> dict[str, list[float]]:
    """symbols: {key: yahoo_symbol} -> {key: [close, ...]} oldest..newest. Missing -> []."""
    out: dict[str, list[float]] = {}
    for key, sym in symbols.items():
        try:
            hist = yf.Ticker(sym).history(period=period)
            closes = [float(x) for x in hist["Close"].dropna().tolist()]
            out[key] = closes
        except Exception as exc:  # noqa: BLE001
            log.warning("yfinance %s (%s) failed: %s", key, sym, exc)
            out[key] = []
    return out
