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
    # Net liquidity FALLING should yield a HIGHER stress metric.
    falling = m.net_liquidity_metric(walcl=[8.0, 7.0], tga=[0.5, 0.5], rrp=[0.5, 0.5])
    rising = m.net_liquidity_metric(walcl=[7.0, 8.0], tga=[0.5, 0.5], rrp=[0.5, 0.5])
    assert falling > rising


def test_last_safe():
    assert m.last([]) is None
    assert m.last([1.0, 2.0]) == 2.0
