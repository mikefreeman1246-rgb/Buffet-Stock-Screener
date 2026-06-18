"""Pure market-weather scoring engine. No I/O — fully unit-testable.

Consumes per-indicator metrics (normalized so HIGHER = MORE STRESS) plus the
active settings (thresholds/weights/rules) and returns an overall 1-5 concern
level mapped to a weather state, with the divergence rules that fired.
"""
from __future__ import annotations

GREEN, YELLOW, RED = 1, 2, 3

WEATHER = {
    1: ("Sunny", "☀️"),
    2: ("Fair", "🌤️"),
    3: ("Cloudy", "☁️"),
    4: ("Stormy", "⛈️"),
    5: ("Hurricane", "🌀"),
}


def classify(metric: float | None, green_max: float, yellow_max: float) -> int | None:
    """Map a stress metric to GREEN/YELLOW/RED (None if no data)."""
    if metric is None:
        return None
    if metric <= green_max:
        return GREEN
    if metric <= yellow_max:
        return YELLOW
    return RED


def score(indicators: dict, settings: dict) -> dict:
    """indicators: {key: {"metric": float|None, ...}}; settings: DEFAULT_WEATHER_SETTINGS shape."""
    thr = settings["thresholds"]
    rules = settings.get("rules", {})

    states = {
        key: classify(indicators.get(key, {}).get("metric"),
                      cfg["green_max"], cfg["yellow_max"])
        for key, cfg in thr.items()
    }

    num = den = 0.0
    for key, cfg in thr.items():
        st = states[key]
        if st is None:
            continue
        num += cfg["weight"] * st
        den += cfg["weight"]
    base = 1.0 if den == 0 else 1.0 + (num / den - 1.0) * 2.0  # 1..3 -> 1..5

    level = base
    fired: list[str] = []

    if rules.get("hidden_hedging") and (
        states.get("skew") == RED
        and states.get("vvix") in (YELLOW, RED)
        and states.get("vix") == GREEN
    ):
        level += 1
        fired.append("hidden_hedging")

    if rules.get("credit_liquidity") and (
        states.get("credit") == RED and states.get("net_liquidity") in (YELLOW, RED)
    ):
        level += 1
        fired.append("credit_liquidity")

    if rules.get("cascade_floor"):
        c = indicators.get("cascade", {})
        if c.get("stocks_down") and c.get("bonds_down") and c.get("gold_down"):
            level = max(level, 4)
            fired.append("cascade_floor")

    final = max(1, min(5, round(level)))
    name, icon = WEATHER[final]
    return {
        "level": final,
        "weather": name,
        "icon": icon,
        "base": round(base, 2),
        "states": states,
        "fired_rules": fired,
        "missing": [k for k, v in states.items() if v is None],
        "read": _read(final, states, fired),
    }


def _read(level: int, states: dict, fired: list[str]) -> str:
    """One-line plain-English summary for the hero banner."""
    reds = [k for k, v in states.items() if v == RED]
    if "hidden_hedging" in fired:
        return "Surface calm, but professionals are buying crash insurance (SKEW/VVIX elevated while VIX low)."
    if "cascade_floor" in fired:
        return "Stocks, bonds and gold falling together — flight-to-quality broken."
    if level <= 1:
        return "Conditions calm across the board."
    if level == 2:
        return "Mostly calm with a few gauges ticking up."
    if level == 3:
        return f"Choppy — watching {', '.join(reds) or 'several gauges'}."
    if level == 4:
        return f"Stormy — {len(reds)} gauges flashing red."
    return "Crisis conditions — broad, simultaneous stress."
