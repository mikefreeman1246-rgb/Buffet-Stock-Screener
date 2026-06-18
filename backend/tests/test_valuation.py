"""Engine tests pinned to the worked examples in the two formula docs.

If any of these fail, the engine no longer matches the source documents.
"""
import math

import pytest

from app.config import Assumptions
from app.services import valuation as V
from app.services.valuation import Fundamentals, Overrides


A = Assumptions()  # doc defaults (Y=5.56, base 8.5, +2g, MoS 25%, r 8.5-11.5, tg 2.5, N=10)


# --------------------------------------------------------------------------- #
# Graham
# --------------------------------------------------------------------------- #
def test_graham_ko_worked_example():
    """graham doc: KO EPS 2.95, g=6, Y=5.56 -> V ~= $47.85."""
    v = V.graham_value(eps=2.95, g_pct=6, a=A)
    assert v == pytest.approx(47.85, abs=0.15)


def test_graham_sweet_spot_is_25pct_discount():
    v = V.graham_value(eps=2.95, g_pct=6, a=A)
    sweet = v * (1 - A.margin_of_safety_pct)
    assert sweet == pytest.approx(v * 0.75, rel=1e-9)


@pytest.mark.parametrize("g,expected_mult", [
    (0, 8.5), (5, 18.5), (10, 28.5), (15, 38.5), (20, 48.5),
])
def test_graham_multiplier_table(g, expected_mult):
    """graham doc 'THE MULTIPLIER EXPLAINED' table."""
    # value / (eps * bond_adj) == multiplier
    eps = 1.0
    bond_adj = 4.4 / A.aaa_bond_yield
    v = V.graham_value(eps=eps, g_pct=g, a=A)
    assert v / (eps * bond_adj) == pytest.approx(expected_mult, rel=1e-9)


@pytest.mark.parametrize("ratio,expected", [
    (0.80, "Undervalued"),
    (0.95, "Fair Value"),
    (1.20, "Mild Overvalued"),
    (1.50, "Overvalued"),
])
def test_graham_verdict_bands(ratio, expected):
    value = 100.0
    price = value * ratio
    assert V.graham_verdict(price, value) == expected


def test_graham_negative_eps_is_na():
    f = Fundamentals(ticker="X", price=10, eps_ttm=-1.0, sector="Industrials")
    out = V.evaluate(f, A)
    assert out["graham_verdict"] == "N/A"
    assert out["graham_value"] is None


# --------------------------------------------------------------------------- #
# Buffett two-stage DCF
# --------------------------------------------------------------------------- #
def test_buffett_g_equals_r_uses_lhopital_branch():
    """When g == r the closed form is singular; engine must use the limit."""
    oe = 10.0
    r = A.r_wide          # 8.5
    g = A.r_wide          # force g == r
    # Compute expected stage-1 via L'Hopital limit, stage-2 explicitly.
    n = A.high_growth_years
    rr = r / 100.0
    tg = A.terminal_growth / 100.0
    s1 = n * oe / (1 + rr)
    terminal = oe * (1 + rr) ** n
    s2 = terminal * (1 + tg) / ((rr - tg) * (1 + rr) ** n)
    expected = s1 + s2
    got = V.buffett_value(oe=oe, g_pct=g, r_pct=r, a=A)
    assert got == pytest.approx(expected, rel=1e-9)
    assert math.isfinite(got)


def test_buffett_value_continuous_near_g_equals_r():
    """The L'Hopital branch must match the closed form as g -> r."""
    near = V.buffett_value(oe=10, g_pct=8.5 + 1e-4, r_pct=8.5, a=A)
    at = V.buffett_value(oe=10, g_pct=8.5, r_pct=8.5, a=A)
    assert near == pytest.approx(at, rel=1e-3)


@pytest.mark.parametrize("ratio,expected", [
    (1.60, "Strong Buy"),
    (1.30, "Buy"),
    (1.00, "Hold"),
    (0.85, "Trim"),
    (0.50, "Pass"),
])
def test_buffett_verdict_bands_no_moat(ratio, expected):
    """buffett doc verdict thresholds, no moat bonus."""
    value = 100.0
    price = value / ratio
    verdict, _ = V.buffett_verdict(value, price, moat="none")
    assert verdict == expected


def test_buffett_wide_moat_bonus_lifts_ratio():
    value, price = 100.0, 100.0
    _, ratio_none = V.buffett_verdict(value, price, moat="none")
    _, ratio_wide = V.buffett_verdict(value, price, moat="wide")
    assert ratio_wide == pytest.approx(ratio_none * 1.05, rel=1e-9)


# --------------------------------------------------------------------------- #
# Financial P/B
# --------------------------------------------------------------------------- #
def test_financial_pb_value_formula():
    """fair_P/B = (ROE - g)/(r - g); V = fair_P/B * book."""
    roe, book = 0.15, 50.0
    g_pct, r_pct = 5.0, 9.5
    val, fair_pb = V.financial_pb_value(roe, g_pct, r_pct, book)
    g, r = 0.05, 0.095
    expected_pb = (roe - g) / (r - g)
    assert fair_pb == pytest.approx(expected_pb, rel=1e-9)
    assert val == pytest.approx(expected_pb * book, rel=1e-9)


def test_financial_pb_does_not_explode_with_high_growth():
    """High short-term growth must not blow up justified P/B (g clamped, P/B capped)."""
    val, fair_pb = V.financial_pb_value(roe=0.18, g_pct=20.0, r_pct=9.5, book_ps=90.0)
    assert fair_pb <= V.PB_CEILING
    assert val == pytest.approx(fair_pb * 90.0, rel=1e-9)


def test_financial_sector_uses_pb_method():
    f = Fundamentals(ticker="BAC", price=40, eps_ttm=3.0, eps_growth=0.05,
                     roe=0.12, book_value_ps=35.0, sector="Financials")
    out = V.evaluate(f, A)
    assert out["buffett_method"] == "pb"
    assert out["buffett_value"] is not None


def test_financial_low_roe_is_na_not_crash():
    """ROE below sustainable growth -> P/B clamps to 0 -> N/A, no ZeroDivision."""
    f = Fundamentals(ticker="X", price=40, eps_ttm=3.0, eps_growth=0.20,
                     roe=0.02, book_value_ps=35.0, sector="Financial Services")
    out = V.evaluate(f, A)
    assert out["buffett_verdict"] == "N/A"
    assert out["buffett_margin_pct"] is None


# --------------------------------------------------------------------------- #
# Owner earnings & moat derivation
# --------------------------------------------------------------------------- #
def test_owner_earnings_cashflow_derivation():
    f = Fundamentals(ticker="X", eps_ttm=5.0, shares_out=100.0,
                     net_income=500.0, dep_amort=200.0, capex=-120.0)
    oe_ps, mult, method = V.owner_earnings_ps(f, Overrides(), eps_base=5.0)
    # maint capex = min(120, 200) = 120 -> OE = 500 + 200 - 120 = 580 -> /100 = 5.8
    assert oe_ps == pytest.approx(5.8, rel=1e-9)
    assert method == "cashflow"
    assert mult == pytest.approx(5.8 / 5.0, rel=1e-9)


def test_oe_multiplier_override_applies_to_eps():
    f = Fundamentals(ticker="X", eps_ttm=8.0)
    oe_ps, mult, method = V.owner_earnings_ps(f, Overrides(oe_multiplier_override=1.2), eps_base=8.0)
    assert oe_ps == pytest.approx(9.6, rel=1e-9)
    assert method == "override"


def test_growth_is_capped():
    f = Fundamentals(ticker="X", eps_growth=0.80)  # 80%
    g = V.effective_growth_pct(f, Overrides(), A.graham_g_cap)
    assert g == A.graham_g_cap  # capped at 20


def test_moat_override_wins():
    f = Fundamentals(ticker="X", roe=0.01)
    assert V.classify_moat(f, Overrides(moat_override="wide")) == "wide"


# --------------------------------------------------------------------------- #
# Dual conviction
# --------------------------------------------------------------------------- #
def test_dual_conviction_max():
    assert V.dual_conviction("Undervalued", "Strong Buy") == "Max Conviction"


def test_dual_conviction_avoid():
    assert V.dual_conviction("Overvalued", "Pass") == "Avoid"


def test_dual_conviction_moat_premium():
    assert V.dual_conviction("Overvalued", "Buy") == "Moat Premium"


# --------------------------------------------------------------------------- #
# Full evaluate() smoke
# --------------------------------------------------------------------------- #
def test_evaluate_full_row_shape():
    f = Fundamentals(ticker="KO", company="Coca-Cola", sector="Consumer Staples",
                     price=81.35, eps_ttm=2.95, eps_growth=0.06, roe=0.40,
                     book_value_ps=6.0, shares_out=4300.0, net_income=10000.0,
                     dep_amort=1100.0, capex=-1500.0, gross_margin=0.60, profit_margin=0.23)
    out = V.evaluate(f, A)
    assert out["graham_value"] == pytest.approx(47.85, abs=0.2)
    assert out["graham_verdict"] == "Overvalued"   # price 81.35 vs ~47.85 -> >135%
    for key in ("buffett_value", "buffett_verdict", "conviction", "moat", "owner_earnings_ps"):
        assert key in out
