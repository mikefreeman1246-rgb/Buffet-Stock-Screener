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
