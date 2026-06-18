from app.config import DEFAULT_WEATHER_SETTINGS
from app.services import weather


def s(metrics, **signals):
    """Build an indicators dict: {key: {"metric": v}} plus cascade signals."""
    ind = {k: {"metric": v} for k, v in metrics.items()}
    if signals:
        ind.setdefault("cascade", {})
        ind["cascade"].update(signals)
    return ind


def test_classify_bands():
    assert weather.classify(10.0, 20.0, 30.0) == weather.GREEN
    assert weather.classify(25.0, 20.0, 30.0) == weather.YELLOW
    assert weather.classify(35.0, 20.0, 30.0) == weather.RED
    assert weather.classify(None, 20.0, 30.0) is None


def test_all_green_is_sunny():
    metrics = {k: c["green_max"] for k, c in DEFAULT_WEATHER_SETTINGS["thresholds"].items()}
    out = weather.score(s(metrics), DEFAULT_WEATHER_SETTINGS)
    assert out["level"] == 1
    assert out["weather"] == "Sunny"


def test_all_red_is_hurricane():
    metrics = {k: c["yellow_max"] + 100 for k, c in DEFAULT_WEATHER_SETTINGS["thresholds"].items()}
    out = weather.score(s(metrics), DEFAULT_WEATHER_SETTINGS)
    assert out["level"] == 5
    assert out["weather"] == "Hurricane"


def test_missing_indicator_excluded():
    # only VIX present and green -> still sunny, no crash
    out = weather.score({"vix": {"metric": 12.0}}, DEFAULT_WEATHER_SETTINGS)
    assert out["level"] == 1
    assert out["states"]["credit"] is None


def test_hidden_hedging_bumps_level():
    # VIX calm (green), but SKEW red + VVIX yellow -> +1 over the calm base
    metrics = {"vix": 14.0, "skew": 150.0, "vvix": 100.0}
    out = weather.score(s(metrics), DEFAULT_WEATHER_SETTINGS)
    assert "hidden_hedging" in out["fired_rules"]
    base_only = weather.score(
        s({"vix": 14.0}), DEFAULT_WEATHER_SETTINGS  # control without hedging combo
    )
    assert out["level"] > base_only["level"]


def test_hidden_hedging_does_not_fire_when_vix_high():
    metrics = {"vix": 35.0, "skew": 150.0, "vvix": 100.0}
    out = weather.score(s(metrics), DEFAULT_WEATHER_SETTINGS)
    assert "hidden_hedging" not in out["fired_rules"]


def test_cascade_floor_sets_min_level_4():
    metrics = {"vix": 12.0}  # otherwise calm
    out = weather.score(s(metrics, stocks_down=True, bonds_down=True, gold_down=True),
                        DEFAULT_WEATHER_SETTINGS)
    assert out["level"] >= 4
    assert "cascade_floor" in out["fired_rules"]


def test_rules_can_be_disabled():
    settings = {**DEFAULT_WEATHER_SETTINGS,
                "rules": {"hidden_hedging": False, "credit_liquidity": False, "cascade_floor": False}}
    metrics = {"vix": 14.0, "skew": 150.0, "vvix": 100.0}
    out = weather.score(s(metrics), settings)
    assert out["fired_rules"] == []


def test_all_yellow_is_cloudy():
    metrics = {k: c["yellow_max"] for k, c in DEFAULT_WEATHER_SETTINGS["thresholds"].items()}
    out = weather.score(s(metrics), DEFAULT_WEATHER_SETTINGS)
    assert out["base"] == 3.0
    assert out["level"] == 3
    assert out["weather"] == "Cloudy"


def test_credit_liquidity_fires_on_red_credit_and_tight_liquidity():
    # credit yellow_max=6.0 -> 8.0 is RED; net_liquidity yellow_max=2.0,
    # green_max=1.0 -> 1.5 is YELLOW (>= yellow triggers the divergence rule)
    metrics = {"credit": 8.0, "net_liquidity": 1.5}
    out = weather.score(s(metrics), DEFAULT_WEATHER_SETTINGS)
    assert "credit_liquidity" in out["fired_rules"]
