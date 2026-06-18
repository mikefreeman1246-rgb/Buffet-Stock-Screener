"""Configuration and default valuation assumptions.

Every default here is sourced directly from the two formula documents in the
project root (graham-valuation-formula.txt, buffett-modernized-formula.txt).
These are the *global* assumptions; they are stored in the `assumptions` table
(seeded from this dataclass) and are user-adjustable at runtime, which is what
makes the screener re-rank live without a data re-pull.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from pathlib import Path

# --- Paths -----------------------------------------------------------------
DATA_DIR = Path("/data") if Path("/data").exists() else Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "stock_screener.db"
_SEED_DIR = Path(__file__).resolve().parent / "data"

# Available universes -> seed file. The pull pipeline picks one of these.
SEED_FILES = {
    "sp500": _SEED_DIR / "sp500.json",
    "sp1500": _SEED_DIR / "sp1500.json",
}
DEFAULT_UNIVERSE = "sp500"
SEED_PATH = SEED_FILES[DEFAULT_UNIVERSE]  # back-compat default

# FRED public CSV for Moody's Seasoned AAA Corporate Bond Yield (no API key).
FRED_AAA_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DAAA"
FRED_FALLBACK_YIELD = 5.56  # doc default (May 2026, Moody's AAA index)

# Sectors treated as financials (justified P/B model, per Buffett doc Mod #4).
FINANCIAL_SECTORS = {"Financials", "Financial Services"}


@dataclass
class Assumptions:
    """Global valuation assumptions. Defaults straight from the docs."""

    # Graham: V = EPS x (base_pe + growth_multiplier * g) x (4.4 / Y)
    aaa_bond_yield: float = FRED_FALLBACK_YIELD   # Y (percent)
    graham_base_pe: float = 8.5                   # no-growth P/E
    graham_growth_multiplier: float = 2.0         # +2 P/E per 1% growth
    graham_g_cap: float = 20.0                    # Graham's practical ceiling (percent)
    margin_of_safety_pct: float = 0.25            # sweet spot = V * (1 - 0.25)

    # Buffett two-stage DCF discount rates by moat (percent)
    r_wide: float = 8.5
    r_moderate: float = 9.5
    r_narrow: float = 10.5
    r_none: float = 11.5
    terminal_growth: float = 2.5                  # GDP-like perpetuity growth (percent)
    high_growth_years: int = 10                   # Stage 1 horizon (N)

    def discount_rate(self, moat: str) -> float:
        return {
            "wide": self.r_wide,
            "moderate": self.r_moderate,
            "narrow": self.r_narrow,
            "none": self.r_none,
        }.get(moat, self.r_none)

    def as_dict(self) -> dict:
        return asdict(self)


DEFAULT_ASSUMPTIONS = Assumptions()

# Server
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
