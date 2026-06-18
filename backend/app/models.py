"""ORM models: stocks snapshot, per-stock overrides, global assumptions, pull status."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Float, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Stock(Base):
    __tablename__ = "stocks"

    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    company: Mapped[str | None] = mapped_column(String)
    sector: Mapped[str | None] = mapped_column(String)
    industry: Mapped[str | None] = mapped_column(String)
    market_cap: Mapped[float | None] = mapped_column(Float)
    price: Mapped[float | None] = mapped_column(Float)
    eps_ttm: Mapped[float | None] = mapped_column(Float)
    eps_growth: Mapped[float | None] = mapped_column(Float)
    roe: Mapped[float | None] = mapped_column(Float)
    book_value_ps: Mapped[float | None] = mapped_column(Float)
    shares_out: Mapped[float | None] = mapped_column(Float)
    net_income: Mapped[float | None] = mapped_column(Float)
    dep_amort: Mapped[float | None] = mapped_column(Float)
    capex: Mapped[float | None] = mapped_column(Float)
    free_cash_flow: Mapped[float | None] = mapped_column(Float)
    gross_margin: Mapped[float | None] = mapped_column(Float)
    profit_margin: Mapped[float | None] = mapped_column(Float)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class Override(Base):
    __tablename__ = "overrides"

    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    growth_override: Mapped[float | None] = mapped_column(Float)
    moat_override: Mapped[str | None] = mapped_column(String)
    oe_multiplier_override: Mapped[float | None] = mapped_column(Float)
    normalized_eps_override: Mapped[float | None] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class Assumption(Base):
    __tablename__ = "assumptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    aaa_bond_yield: Mapped[float] = mapped_column(Float)
    graham_base_pe: Mapped[float] = mapped_column(Float)
    graham_growth_multiplier: Mapped[float] = mapped_column(Float)
    graham_g_cap: Mapped[float] = mapped_column(Float)
    margin_of_safety_pct: Mapped[float] = mapped_column(Float)
    r_wide: Mapped[float] = mapped_column(Float)
    r_moderate: Mapped[float] = mapped_column(Float)
    r_narrow: Mapped[float] = mapped_column(Float)
    r_none: Mapped[float] = mapped_column(Float)
    terminal_growth: Mapped[float] = mapped_column(Float)
    high_growth_years: Mapped[int] = mapped_column(Integer)


class StockTag(Base):
    """A user-defined free-form tag on a stock. A stock can have many."""
    __tablename__ = "stock_tags"

    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    tag: Mapped[str] = mapped_column(String, primary_key=True)


class PullStatus(Base):
    __tablename__ = "pull_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str | None] = mapped_column(String)       # running|completed|failed|paused
    total: Mapped[int | None] = mapped_column(Integer)
    completed: Mapped[int | None] = mapped_column(Integer)
    failed: Mapped[int | None] = mapped_column(Integer)
    last_ticker: Mapped[str | None] = mapped_column(String)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class MarketSnapshot(Base):
    __tablename__ = "market_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pulled_at: Mapped[datetime | None] = mapped_column(DateTime)
    payload: Mapped[str | None] = mapped_column(Text)   # JSON: indicators + score


class MarketSettings(Base):
    __tablename__ = "market_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    payload: Mapped[str | None] = mapped_column(Text)   # JSON: thresholds + rules
