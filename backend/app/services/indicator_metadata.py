"""Market indicator metadata and analysis functions.

Keys here MUST match the threshold keys in DEFAULT_WEATHER_SETTINGS (config.py):
  credit, cascade, treasuries, net_liquidity, financial_stress,
  skew, nfci, vvix, air_pocket, vix, gold, oil
"""

INDICATOR_METADATA = {
    "credit": {
        "label": "HY Credit Spreads",
        "unit": "%",
        "weight": 7,
        "description": (
            "High-yield (junk) bond yield spread over equivalent US Treasuries. "
            "Measures the extra yield investors demand to hold risky corporate debt. "
            "Tighter spreads = risk-on confidence; wider spreads = credit stress and risk-off."
        ),
        "healthy": "Spreads tight (≤ 4%), indicating healthy credit appetite and optimistic risk sentiment. Capital flows freely to corporations.",
        "watch": "Spreads moderately elevated (4–6%), suggesting caution. Credit costs rising but no acute stress — monitor for widening.",
        "chaos": "Spreads very wide (> 6%), signaling panic selling, credit deterioration, or acute risk-off. Corporate borrowing freezes.",
        "implications": {
            "short_term": "Widening spreads trigger flight-to-quality flows — equities weaken, Treasuries rally, volatility spikes. Expect turbulence within days.",
            "long_term": "Persistent wide spreads choke corporate investment, weaken earnings, and often precede recession by 6–12 months.",
            "bullish_threshold": "Spreads tighten decisively after widening, confirming sentiment recovery and renewed risk appetite.",
            "bearish_threshold": "Spreads break above 6% on volume, often preceding equity drawdowns of 10%+ over following weeks.",
        },
        "typical_ranges": {
            "normal_market": "3–4%",
            "elevated_caution": "4–6%",
            "crisis_level": "7–10%+ (2008/2020 levels)",
        },
    },

    "cascade": {
        "label": "Cascade Risk",
        "unit": "",
        "weight": 6,
        "description": (
            "Measures contagion risk by tracking whether multiple asset classes are falling simultaneously. "
            "When stocks, bonds, and gold all decline together, traditional diversification breaks down — "
            "signaling forced selling, margin calls, or a liquidity crisis. "
            "Scored 1–3 based on how many of the three core assets are declining over the past 5 trading days, "
            "with an amplifier when HY credit spreads are widening AND VVIX exceeds 110."
        ),
        "healthy": "0–1 of 3 assets falling (score 1). Normal market rotation — declines are isolated, not systemic. Safe havens are functioning.",
        "watch": "2 of 3 assets falling (score 2), OR credit spreads widening simultaneously with VVIX > 110. Contagion risk building; diversification eroding.",
        "chaos": "All 3 assets falling together (score 3). True liquidity crisis — investors forced to sell everything for cash. No safe havens. Matches March 2020, 2008 conditions.",
        "components": [
            {
                "name": "SPX (S&P 500)",
                "signal": "Falling over 5 trading days",
                "role": "Equity leg — primary risk-asset barometer. Falling equity confirms risk-off pressure.",
            },
            {
                "name": "TLT (20-Year Treasury ETF)",
                "signal": "Falling over 5 trading days",
                "role": "Bond leg — safe-haven gauge. Bonds falling alongside stocks removes the traditional hedge, amplifying contagion risk.",
            },
            {
                "name": "Gold",
                "signal": "Falling over 5 trading days",
                "role": "Gold leg — inflation/crisis hedge. Gold falling with stocks signals pure liquidity liquidation, not just recession fear.",
            },
            {
                "name": "HY Credit Spreads",
                "signal": "Spreads widening (rising) over 5 days",
                "role": "Credit stress amplifier — rising spreads combined with VVIX stress escalate score from 1→2 even without full asset triad.",
            },
            {
                "name": "VVIX",
                "signal": "VVIX > 110",
                "role": "Volatility amplifier — extreme vol-of-vol above 110 combined with credit stress triggers Yellow regardless of asset count.",
            },
        ],
        "scoring": {
            "1_green": "0–1 of 3 assets (SPX/TLT/Gold) falling",
            "2_yellow": "2 of 3 assets falling  — OR —  credit spreads rising + VVIX > 110",
            "3_red": "All 3 assets (SPX + TLT + Gold) falling simultaneously",
        },
        "implications": {
            "short_term": "Score 2+ triggers forced deleveraging waves — expect gap-down opens, wide bid-ask spreads, and stop-loss cascades within 1–5 days.",
            "long_term": "Score 3 events historically mark capitulation bottoms (March 2020, Oct 2008) but require months of recovery. Credit markets seize first.",
            "bullish_threshold": "Score drops from 2→1 as at least one asset class stabilizes, confirming contagion is not spreading.",
            "bearish_threshold": "Score reaches 3 with all three legs falling — historically accompanies 15–40% peak-to-trough drawdowns.",
        },
        "typical_ranges": {
            "normal": "Score 1 (most of the time)",
            "stress_episode": "Score 2 (several times per year during corrections)",
            "crisis": "Score 3 (rare — roughly 2–4 times per decade)",
        },
        "historical_examples": {
            "March_2020_COVID": "Score 3 — stocks, bonds, and gold all liquidated in the dash-for-cash phase before Fed intervention.",
            "Oct_2008_GFC": "Score 3 — simultaneous collapse across all asset classes as Lehman contagion spread.",
            "2022_Rate_Shock": "Score 2 — stocks and bonds fell together (negative correlation broke down) but gold held partial safe-haven role.",
        },
    },

    "treasuries": {
        "label": "10Y Move (bps/wk)",
        "unit": "bps",
        "weight": 6,
        "description": (
            "Weekly change in the 10-year US Treasury yield in basis points (bps). "
            "Measures the speed of interest rate repricing — large moves signal uncertainty, "
            "forced repositioning, or policy shocks. Direction matters less than magnitude."
        ),
        "healthy": "Small weekly moves (≤ 15 bps), indicating stable rate expectations and orderly bond markets. Duration risk is manageable.",
        "watch": "Moderate moves (15–30 bps/week), suggesting elevated uncertainty. Fixed income portfolios under pressure; equity multiples at risk.",
        "chaos": "Large moves (> 30 bps/week), indicating panic repricing, Fed surprise, or geopolitical shock. Bond market dislocations spill into equities.",
        "implications": {
            "short_term": "Large 10Y moves destabilize equity valuations (via discount rate) and can trigger mortgage/credit market stress within days.",
            "long_term": "Sustained large moves signal broken price discovery — central banks may need to intervene to restore order.",
            "bullish_threshold": "Moves calm below 10 bps/week after a volatile period, indicating rate environment stabilizing.",
            "bearish_threshold": "Multi-week moves above 25 bps often accompany equity corrections of 5–15%.",
        },
        "typical_ranges": {
            "calm_market": "5–10 bps/week",
            "elevated": "15–25 bps/week",
            "crisis_repricing": "30–60+ bps/week (e.g., March 2020, 2022 rate shock)",
        },
    },

    "net_liquidity": {
        "label": "Net Liquidity",
        "unit": "T",
        "weight": 5,
        "description": (
            "Federal Reserve net liquidity: the Fed balance sheet minus the Treasury General Account (TGA) "
            "and the Reverse Repo (RRP) facility. Represents cash actively circulating in financial markets. "
            "Rising = more liquidity supporting asset prices; falling = tightening that pressures valuations."
        ),
        "healthy": "Net liquidity flat or rising (≤ 1.5T withdrawn), providing market cushion and supporting risk asset valuations.",
        "watch": "Net liquidity declining meaningfully (1.5–4T range), suggesting tightening conditions. Asset prices vulnerable to re-rating.",
        "chaos": "Net liquidity sharply negative or collapsing (> 4T withdrawn), often forcing fire sales and deleveraging across markets.",
        "implications": {
            "short_term": "Rapid liquidity withdrawal can trigger margin calls and flash crashes within days as collateral values shrink.",
            "long_term": "Persistent negative net liquidity constrains equity multiples, credit availability, and GDP growth over quarters.",
            "bullish_threshold": "Fed announces QE, repos, or TGA drawdowns that inject liquidity — historically marks major equity bottoms.",
            "bearish_threshold": "Net liquidity falls more than $200B in a single week without compensating market support mechanisms.",
        },
        "typical_ranges": {
            "expansionary_QE": "Positive / rising rapidly",
            "neutral": "Flat ± $200B",
            "tightening_QT": "Declining steadily",
        },
    },

    "financial_stress": {
        "label": "OFR Fin. Stress",
        "unit": "",
        "weight": 5,
        "description": (
            "Office of Financial Research (OFR) Financial Stress Index — a daily composite of "
            "18 market-based indicators across credit markets, equity volatility, funding markets, "
            "safe-haven demand, and risk appetite. Positive values = stress above historical norm; "
            "negative = below-average stress."
        ),
        "healthy": "Index at or below 0 — financial conditions loose, credit flowing, funding markets calm. Below-average systemic stress.",
        "watch": "Index 0–2 — elevated stress. One or more subsectors (credit, funding, or equity vol) showing strain.",
        "chaos": "Index above 2 — acute systemic stress across multiple subsectors simultaneously. Matches 2008/2020 crisis readings.",
        "implications": {
            "short_term": "Stress spikes above 1 trigger immediate volatility, forced selling, and margin pressure within 1–2 weeks.",
            "long_term": "Sustained readings above 1 restrict credit to the real economy, weakening hiring and investment over quarters.",
            "bullish_threshold": "Index drops below 0 after a stress episode, confirming systemic healing and return to normal conditions.",
            "bearish_threshold": "Index exceeds 2, matching 2008 financial crisis and March 2020 COVID shock peak readings.",
        },
        "typical_ranges": {
            "calm": "-0.5 to 0",
            "moderate_stress": "0 to 1",
            "severe_crisis": "2+ (2008 GFC, March 2020)",
        },
    },

    "skew": {
        "label": "SKEW",
        "unit": "",
        "weight": 5,
        "description": (
            "CBOE SKEW Index measures the cost of buying out-of-the-money S&P 500 put options "
            "relative to at-the-money options. Elevated SKEW means investors are paying a premium "
            "to hedge against large tail-risk drawdowns — a sign of sophisticated money fearing "
            "a sudden crash even when VIX is low."
        ),
        "healthy": "SKEW ≤ 130 — low tail-risk hedging demand. Market participants not aggressively protecting against crash scenarios.",
        "watch": "SKEW 130–145 — rising demand for downside protection. Smart money hedging against potential fat-tail events.",
        "chaos": "SKEW > 145 — extreme tail-risk hedging. Significant positioning for a sudden large market dislocation.",
        "implications": {
            "short_term": "Rising SKEW with low VIX is a 'calm before the storm' signal — volatility may spike suddenly with little warning.",
            "long_term": "Persistently elevated SKEW reflects underlying fragility and hidden leverage that markets are pricing but not yet pricing in VIX.",
            "bullish_threshold": "SKEW drops below 120 — hedging demand normalizing, tail-risk fears receding.",
            "bearish_threshold": "SKEW exceeds 150 with VIX still low — historically precedes sharp, sudden corrections.",
        },
        "typical_ranges": {
            "complacent": "100–120",
            "cautious": "125–140",
            "extreme_hedging": "145+ (rare)",
        },
    },

    "nfci": {
        "label": "NFCI",
        "unit": "",
        "weight": 4,
        "description": (
            "Chicago Fed National Financial Conditions Index — weekly composite of 105 measures "
            "across money markets, debt markets, and equity markets. "
            "Negative values = looser than average financial conditions; "
            "positive values = tighter than average, which historically precedes recessions."
        ),
        "healthy": "NFCI ≤ -0.2 — looser than average conditions. Credit accessible, funding markets calm, equity volatility low.",
        "watch": "NFCI -0.2 to 0 — conditions tightening toward average. Borrowing costs rising; watch for deterioration.",
        "chaos": "NFCI > 0 — tighter than average. Credit stress building; historically precedes GDP contraction within 1–4 quarters.",
        "implications": {
            "short_term": "Rising NFCI tightens credit for consumers and businesses — expect earnings pressure and equity weakness within weeks.",
            "long_term": "NFCI above 0 sustained for 2+ quarters historically precedes recession. A leading recession indicator.",
            "bullish_threshold": "NFCI drops below -0.5, signaling very loose conditions that historically support strong equity returns.",
            "bearish_threshold": "NFCI exceeds +0.5, matching conditions seen 6–12 months before the 2008 and 2020 recessions.",
        },
        "typical_ranges": {
            "expansionary": "-0.8 to -0.2",
            "neutral": "-0.2 to 0",
            "restrictive": "0 to +1 (recession warning zone)",
        },
    },

    "vvix": {
        "label": "VVIX",
        "unit": "",
        "weight": 4,
        "description": (
            "Volatility of VIX — measures how rapidly the VIX (fear gauge) itself is changing. "
            "High VVIX means VIX is becoming unpredictable and unstable, often signaling that "
            "the market is entering an unstable volatility regime where normal hedging breaks down."
        ),
        "healthy": "VVIX ≤ 90 — VIX moving in an orderly, predictable range. Options market functioning normally.",
        "watch": "VVIX 90–110 — VIX becoming more erratic. Hedging costs rising; market makers widening spreads.",
        "chaos": "VVIX > 110 — extreme VIX instability. Signals potential volatility regime change; options pricing breaks down. Also used as a cascade risk amplifier.",
        "implications": {
            "short_term": "VVIX spikes often precede sharp intraday VIX moves and equity whipsaws — difficult to hedge effectively.",
            "long_term": "Sustained high VVIX reflects broken price discovery and structural market fragility.",
            "bullish_threshold": "VVIX drops below 80 — volatility regime stabilizing, hedging costs normalizing.",
            "bearish_threshold": "VVIX exceeds 120 — matches conditions seen during flash crashes and major dislocations.",
        },
        "typical_ranges": {
            "stable": "60–85",
            "elevated": "90–110",
            "crisis_regime": "115+ (flash crash / systemic event)",
        },
    },

    "air_pocket": {
        "label": "Air Pocket Risk",
        "unit": "",
        "weight": 4,
        "description": (
            "Composite measure of sudden large-drop risk — conditions where market liquidity "
            "can evaporate instantly, causing gap-down moves with no buyers. "
            "Scored 1–3, combining thin market depth signals with elevated volatility regimes. "
            "Score 2+ means the market is vulnerable to a flash-crash style move."
        ),
        "healthy": "Score 1 — market depth adequate, volatility regime stable. Large sudden drops unlikely.",
        "watch": "Score 2 — liquidity thinning or volatility elevated. Vulnerable to gap moves; reduce position sizing.",
        "chaos": "Score 3 — air pocket conditions present. High probability of sudden 2–5% intraday drop with no warning.",
        "implications": {
            "short_term": "Rising air pocket risk triggers wide bid-ask spreads, stop-loss cascades, and slippage on large orders.",
            "long_term": "Structural air pocket risk reflects low market resilience — systemic fragility building.",
            "bullish_threshold": "Score drops to 1 — liquidity restored, market depth returning to normal.",
            "bearish_threshold": "Score reaches 3 — historically accompanies sudden flash-crash type events.",
        },
        "typical_ranges": {
            "normal": "Score 1 (most trading days)",
            "elevated_risk": "Score 2 (corrections, thin holiday markets)",
            "flash_crash_zone": "Score 3 (rare acute events)",
        },
    },

    "vix": {
        "label": "VIX",
        "unit": "",
        "weight": 3,
        "description": (
            "CBOE Volatility Index — the market's 30-day implied volatility expectation for the S&P 500, "
            "derived from options prices. Known as the 'fear gauge.' "
            "Low VIX = complacency; high VIX = fear and uncertainty. "
            "VIX tends to spike suddenly and mean-revert, making timing critical."
        ),
        "healthy": "VIX ≤ 20 — calm markets, low fear, favorable conditions for risk-on positioning.",
        "watch": "VIX 20–30 — elevated concern. Hedging demand rising; expect larger intraday swings.",
        "chaos": "VIX > 30 — panic conditions. Forced selling, margin calls, extreme bid-ask spreads. Crisis-level fear.",
        "implications": {
            "short_term": "VIX spikes above 30 often mark short-term capitulation bottoms — but can overshoot to 40–80 in true crises.",
            "long_term": "Sustained VIX above 25 reflects genuine growth fears or policy uncertainty, weighing on equity multiples.",
            "bullish_threshold": "VIX drops below 15 after a spike — historically marks resumption of bull market conditions.",
            "bearish_threshold": "VIX exceeds 35 — matches 2008, 2011, 2020 crisis conditions with significant drawdown risk.",
        },
        "typical_ranges": {
            "bull_market": "12–18",
            "correction": "20–30",
            "crisis": "35–80+ (2008 peak: 80, March 2020 peak: 65)",
        },
    },

    "gold": {
        "label": "Gold (% / mo)",
        "unit": "%",
        "weight": 2,
        "description": (
            "Monthly percentage change in gold prices (spot). "
            "Gold rises during risk-off, inflation fears, dollar weakness, and geopolitical crises. "
            "Gold falling while stocks also fall is a key cascade risk signal (no safe haven). "
            "Gold rising with stocks = inflationary or geopolitical premium being priced."
        ),
        "healthy": "Gold monthly change ≤ 5% — stable to modest moves. Not pricing in acute crisis or runaway inflation.",
        "watch": "Gold +5–10% per month — meaningful safe-haven or inflation premium forming. Watch for equity divergence.",
        "chaos": "Gold > 10% per month — acute flight-to-safety or inflation shock. Geopolitical or systemic stress being priced aggressively.",
        "implications": {
            "short_term": "Gold spikes often accompany equity selloffs and policy shocks — can provide portfolio cushion if held.",
            "long_term": "Multi-month gold uptrends reflect structural loss of confidence in fiat currency or central bank credibility.",
            "bullish_threshold": "Gold peaks and rolls over while equities stabilize — crisis premium unwinding.",
            "bearish_threshold": "Gold falls alongside stocks and bonds — cascade risk signal (all safe havens failing simultaneously).",
        },
        "typical_ranges": {
            "calm": "±2% per month",
            "trending": "3–6% per month",
            "crisis_spike": "8–15% per month",
        },
    },

    "oil": {
        "label": "Oil (WTI)",
        "unit": "$",
        "weight": 1,
        "description": (
            "West Texas Intermediate (WTI) crude oil price in USD per barrel. "
            "Oil is a dual signal: rising prices can signal strong demand (bullish) OR supply shock/geopolitical risk (stagflationary). "
            "Falling oil signals weak demand (recession risk) or supply glut. Context determines interpretation."
        ),
        "healthy": "WTI ≤ $90/bbl — manageable energy costs supporting consumer spending and corporate margins.",
        "watch": "WTI $90–$110/bbl — elevated energy costs pressuring inflation and consumer confidence.",
        "chaos": "WTI > $110/bbl — energy shock territory. Stagflationary pressure; central banks face growth/inflation dilemma.",
        "implications": {
            "short_term": "Oil spikes above $100 quickly feed into headline CPI, pressuring Fed policy and equity valuations within weeks.",
            "long_term": "Sustained high oil historically precedes recessions (1973, 1979, 1990, 2008) by 6–18 months.",
            "bullish_threshold": "Oil moderates to $70–85 range — energy headwinds easing, inflation pressure declining.",
            "bearish_threshold": "Oil breaks above $120 — matches 2022 Ukraine shock; stagflation risk rises sharply.",
        },
        "typical_ranges": {
            "low_demand_glut": "$50–70/bbl",
            "normal_range": "$70–90/bbl",
            "geopolitical_premium": "$100–130/bbl",
        },
    },
}


def get_indicator_info(key: str) -> dict:
    """Get metadata for a single indicator."""
    return INDICATOR_METADATA.get(key, {})


def get_all_indicator_info() -> dict:
    """Get metadata for all indicators."""
    return INDICATOR_METADATA


def analyze_market_health(indicators: dict, states: dict, score_level: str) -> dict:
    """
    Synthesize market health from individual indicator states.

    Args:
        indicators: dict of indicator keys to Indicator objects with value/trend
        states: dict of indicator keys to state values (1=GREEN, 2=YELLOW, 3=RED)
        score_level: overall score level string ("bullish", "neutral", "bearish")

    Returns:
        dict with health, short_term outlook, long_term outlook, signal breakdown, risks, opportunities
    """
    healthy_count = sum(1 for s in states.values() if s == 1)
    watch_count = sum(1 for s in states.values() if s == 2)
    chaos_count = sum(1 for s in states.values() if s == 3)
    total_count = len(states)

    health_map = {"bullish": "Bullish", "neutral": "Neutral", "bearish": "Bearish"}
    health = health_map.get(score_level, "Unknown")

    if chaos_count > 3:
        short_term_dir = "Bearish"
        short_term_reasoning = "Multiple indicators in chaos; expect downside risk."
        short_term_horizon = "1–4 weeks"
    elif watch_count > 4:
        short_term_dir = "Cautious"
        short_term_reasoning = "Mixed signals with elevated caution; downside bias."
        short_term_horizon = "1–4 weeks"
    elif healthy_count >= total_count - 2:
        short_term_dir = "Bullish"
        short_term_reasoning = "Most indicators healthy; positive momentum expected."
        short_term_horizon = "1–4 weeks"
    else:
        short_term_dir = "Neutral"
        short_term_reasoning = "Balanced signals; direction unclear."
        short_term_horizon = "1–4 weeks"

    if chaos_count > 2 and watch_count > 3:
        long_term_dir = "Bearish"
        long_term_reasoning = "Accumulating stress indicators suggest longer-term headwinds."
        long_term_horizon = "3–12 months"
    elif healthy_count < 4:
        long_term_dir = "Cautious"
        long_term_reasoning = "Fragility building; risk of deterioration over months."
        long_term_horizon = "3–12 months"
    elif healthy_count >= total_count - 2:
        long_term_dir = "Bullish"
        long_term_reasoning = "Strong fundamentals suggest sustained upside bias."
        long_term_horizon = "3–12 months"
    else:
        long_term_dir = "Neutral"
        long_term_reasoning = "Mixed signals; no clear multi-month trend."
        long_term_horizon = "3–12 months"

    top_risks = []
    for key, state in states.items():
        if state in [2, 3]:
            meta = get_indicator_info(key)
            if meta:
                label = meta.get("label", key)
                top_risks.append(f"{label} {'in chaos state' if state == 3 else 'elevated risk'}")
    top_risks = top_risks[:3]

    opportunities = []
    if healthy_count > 6:
        opportunities.append("Broad-based indicator health supports constructive positioning")
    if "vix" in indicators and states.get("vix") == 1:
        opportunities.append("Low volatility provides entry opportunity window")
    if "credit" in indicators and states.get("credit") == 1:
        opportunities.append("Tight credit spreads indicate strong credit demand")

    return {
        "health": health,
        "short_term": {
            "direction": short_term_dir,
            "reasoning": short_term_reasoning,
            "horizon": short_term_horizon,
        },
        "long_term": {
            "direction": long_term_dir,
            "reasoning": long_term_reasoning,
            "horizon": long_term_horizon,
        },
        "signal_breakdown": {
            "healthy_count": healthy_count,
            "watch_count": watch_count,
            "chaos_count": chaos_count,
            "total_count": total_count,
        },
        "top_risks": top_risks,
        "opportunities": opportunities,
    }
