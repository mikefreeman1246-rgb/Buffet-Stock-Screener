from app.services import market_service as m


def test_pct_change_month():
    # ~21 trading days; +10% from first to last
    series = [100.0] * 21 + [110.0]
    assert round(m.pct_change(series, lookback=21), 1) == 10.0


def test_bps_change_week():
    # yield 4.00 -> 4.25 over 5 sessions = +25 bps
    series = [4.00, 4.05, 4.10, 4.15, 4.20, 4.25]
    assert round(m.bps_change(series, lookback=5), 0) == 25.0


def test_net_liquidity_metric_inverts_direction():
    # Realistic magnitudes: WALCL/WTREGEN in millions (~$6.7T / $0.8T), RRP in
    # billions (~$7B). Net liquidity FALLING -> HIGHER (positive) stress metric.
    falling = m.net_liquidity_metric(
        walcl=[6_700_000, 6_600_000], tga=[800_000, 800_000], rrp=[7.0, 7.0])
    rising = m.net_liquidity_metric(
        walcl=[6_600_000, 6_700_000], tga=[800_000, 800_000], rrp=[7.0, 7.0])
    assert falling > 0 > rising
    assert falling > rising


def test_net_liquidity_metric_is_percent_drain():
    # A net-liquidity drain over the window reads as a positive % stress (here
    # ~$136B off ~$6.0T net ≈ +2.3%), confirming the metric is in a % domain.
    walcl = [6_800_000] * 5 + [6_664_000]
    metric = m.net_liquidity_metric(walcl=walcl, tga=[800_000] * 6, rrp=[7.0])
    assert 2.0 < metric < 2.5


def test_net_liquidity_flat_is_green():
    # Flat liquidity -> metric near zero (well inside the green band, < 1.5).
    metric = m.net_liquidity_metric(
        walcl=[6_700_000] * 6, tga=[800_000] * 6, rrp=[7.0])
    assert abs(metric) < 0.01


def test_last_safe():
    assert m.last([]) is None
    assert m.last([1.0, 2.0]) == 2.0


def test_cascade_excluded_when_feeds_unavailable():
    # Full feed outage: cascade has no data to judge, so it must exclude
    # itself from the score (metric is None) rather than fabricating green.
    card = m._cascade({}, {})
    assert card["metric"] is None
    assert card["stocks_down"] is False
    assert card["bonds_down"] is False
    assert card["gold_down"] is False
