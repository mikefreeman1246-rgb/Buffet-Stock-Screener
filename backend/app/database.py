"""SQLAlchemy engine + session + schema init/seed."""
from __future__ import annotations

import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import DB_PATH, DEFAULT_ASSUMPTIONS, DEFAULT_WEATHER_SETTINGS
from app.models import Base, Assumption, MarketSettings

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)
    _seed_assumptions()
    _seed_market_settings()


def _seed_assumptions() -> None:
    """Ensure the single global assumptions row exists (id=1)."""
    with SessionLocal() as db:
        if db.get(Assumption, 1) is None:
            db.add(Assumption(id=1, **DEFAULT_ASSUMPTIONS.as_dict()))
            db.commit()


def _seed_market_settings() -> None:
    """Ensure the single market settings row exists (id=1)."""
    with SessionLocal() as db:
        if db.get(MarketSettings, 1) is None:
            db.add(MarketSettings(id=1, payload=json.dumps(DEFAULT_WEATHER_SETTINGS)))
            db.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
