"""Pull per-stock fundamentals + cash-flow from Yahoo via yfinance (free, no key).

Each call returns a plain dict matching the `stocks` table / Fundamentals
shape. Robust to missing fields — anything unavailable comes back as None
rather than raising, so one bad ticker never breaks a pull.
"""
from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)


def _row(df: Optional[pd.DataFrame], *labels: str) -> Optional[float]:
    """First matching row's most-recent (column 0) value, or None."""
    if df is None or df.empty:
        return None
    for label in labels:
        if label in df.index:
            try:
                val = df.loc[label].iloc[0]
                if pd.notna(val):
                    return float(val)
            except Exception:  # noqa: BLE001
                continue
    return None


def _eps_cagr(financials: Optional[pd.DataFrame]) -> Optional[float]:
    """Historical diluted-EPS CAGR (decimal) as a growth fallback."""
    if financials is None or financials.empty:
        return None
    for label in ("Diluted EPS", "Basic EPS"):
        if label in financials.index:
            series = financials.loc[label].dropna()
            if len(series) >= 2:
                latest, oldest = float(series.iloc[0]), float(series.iloc[-1])
                years = len(series) - 1
                if oldest > 0 and latest > 0 and years > 0:
                    return (latest / oldest) ** (1 / years) - 1
    return None


def fetch_fundamentals(ticker: str, company: str = "", sector: str = "") -> dict:
    """Fetch one ticker. Returns a dict; raises only on total failure."""
    yt = yf.Ticker(ticker)
    info = yt.info or {}
    try:
        cashflow = yt.cashflow
    except Exception:  # noqa: BLE001
        cashflow = None
    try:
        financials = yt.financials
    except Exception:  # noqa: BLE001
        financials = None

    eps_growth = info.get("earningsGrowth")
    if eps_growth is None:
        eps_growth = _eps_cagr(financials)

    net_income = _row(financials, "Net Income", "Net Income Common Stockholders")
    if net_income is None:
        net_income = info.get("netIncomeToCommon")

    return {
        "ticker": ticker,
        "company": info.get("longName") or info.get("shortName") or company,
        "sector": info.get("sector") or sector,
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "eps_ttm": info.get("trailingEps"),
        "eps_growth": eps_growth,
        "roe": info.get("returnOnEquity"),
        "book_value_ps": info.get("bookValue"),
        "shares_out": info.get("sharesOutstanding"),
        "net_income": net_income,
        "dep_amort": _row(cashflow, "Depreciation And Amortization",
                          "Depreciation Amortization Depletion", "Depreciation"),
        "capex": _row(cashflow, "Capital Expenditure", "Purchase Of PPE"),
        "free_cash_flow": _row(cashflow, "Free Cash Flow"),
        "gross_margin": info.get("grossMargins"),
        "profit_margin": info.get("profitMargins"),
    }
