"""Market indicator metadata and analysis functions."""

INDICATOR_METADATA = {
    "hy_credit_spreads": {
        "label": "HY Credit Spreads",
        "unit": "bps",
        "weight": 1.0,
        "description": "High-yield bond credit spreads relative to Treasury yields. Tighter spreads indicate risk-on sentiment; wider spreads signal stress.",
        "healthy": "Spreads tight (< 400 bps), indicating healthy credit demand and optimistic risk appetite.",
        "watch": "Spreads moderately elevated (400-500 bps), suggesting cautious sentiment but no acute stress.",
        "chaos": "Spreads very wide (> 500 bps), indicating panic selling, credit deterioration, or sudden risk-off.",
        "implications": {
            "short_term": "Wide spreads trigger flight-to-quality flows; expect equity weakness and volatility spikes.",
            "long_term": "Persistent wide spreads can signal economic slowdown or upcoming recession.",
            "bullish_threshold": "Spreads tighten after widening, showing healing sentiment.",
            "bearish_threshold": "Spreads break above 450 bps on sudden news, often preceding equity sell-offs.",
        },
        "typical_ranges": {
            "normal": "300–400 bps",
            "stress": "500+ bps",
            "extreme": "700+ bps (financial crisis level)",
        },
    },
    "cascade_risk": {
        "label": "Cascade Risk",
        "unit": "%",
        "weight": 0.9,
        "description": "Measure of systemic risk from interconnected financial institution failures. Rising cascade risk signals contagion potential.",
        "healthy": "Low cascade risk (< 20%), indicating isolated failures won't trigger systemic spread.",
        "watch": "Moderate cascade risk (20–40%), suggesting careful monitoring of interconnections.",
        "chaos": "High cascade risk (> 40%), indicating significant contagion risk.",
        "implications": {
            "short_term": "Rising cascade risk can trigger sudden credit market freezes and liquidity crunches.",
            "long_term": "Sustained high cascade risk weakens credit availability and GDP growth.",
            "bullish_threshold": "Cascade risk declines below 25%, showing reduced systemic fragility.",
            "bearish_threshold": "Cascade risk jumps above 35% on stress events.",
        },
        "typical_ranges": {
            "normal": "15–25%",
            "stress": "30–50%",
            "extreme": "50%+ (financial crisis contagion)",
        },
    },
    "ten_year_move": {
        "label": "10Y Move",
        "unit": "bps/day",
        "weight": 0.7,
        "description": "Daily volatility of 10-year Treasury yields. High volatility suggests uncertainty and rapid repricing.",
        "healthy": "Low yield volatility (< 4 bps/day), indicating stable rate expectations.",
        "watch": "Moderate volatility (4–7 bps/day), suggesting elevated uncertainty.",
        "chaos": "High volatility (> 7 bps/day), indicating panic repricing or shock events.",
        "implications": {
            "short_term": "High 10Y volatility often precedes equity market dislocations.",
            "long_term": "Sustained high volatility signals broken price discovery.",
            "bullish_threshold": "Volatility drops after spikes, showing stabilization.",
            "bearish_threshold": "Multi-day spikes above 8 bps often accompany Fed surprises or geopolitical shocks.",
        },
        "typical_ranges": {
            "normal": "2–4 bps",
            "stress": "6–10 bps",
            "extreme": "15+ bps (crisis moves)",
        },
    },
    "net_liquidity": {
        "label": "Net Liquidity",
        "unit": "$B",
        "weight": 1.0,
        "description": "Fed's net liquidity provision via repos, QE, and balance sheet changes. Negative values indicate withdrawals (tightening).",
        "healthy": "Positive/flat net liquidity, providing market cushion.",
        "watch": "Declining net liquidity, suggesting potential tightness ahead.",
        "chaos": "Sharply negative net liquidity, often forcing fire sales and deleveraging.",
        "implications": {
            "short_term": "Liquidity withdrawal can trigger flash crashes or margin calls within days.",
            "long_term": "Persistent negative liquidity constrains asset valuations and credit growth.",
            "bullish_threshold": "Fed announces balance sheet expansion or QE, reversing liquidity drain.",
            "bearish_threshold": "Fed drains $ 50B+ weekly without corresponding market stabilization.",
        },
        "typical_ranges": {
            "normal": "0 to +200B",
            "stress": "-100B to -50B",
            "extreme": "-200B+ (emergency measures needed)",
        },
    },
    "ofr_stress": {
        "label": "OFR Financial Stress",
        "unit": "index",
        "weight": 0.8,
        "description": "Office of Financial Research stress index combining credit, equity, funding, and valuation measures.",
        "healthy": "Low stress index (< 0.5), indicating calm conditions.",
        "watch": "Moderate stress (0.5–1.0), suggesting unease.",
        "chaos": "High stress (> 1.0), indicating acute systemic strain.",
        "implications": {
            "short_term": "Stress spikes often trigger immediate volatility and forced selling.",
            "long_term": "Sustained high stress restricts credit and economic activity.",
            "bullish_threshold": "Stress index declines below 0.5 after spike.",
            "bearish_threshold": "Stress index exceeds 0.9, matching 2008/2020 levels.",
        },
        "typical_ranges": {
            "normal": "0.2–0.5",
            "stress": "0.8–1.2",
            "extreme": "1.5+ (financial crisis)",
        },
    },
    "skew": {
        "label": "SKEW",
        "unit": "index",
        "weight": 0.6,
        "description": "Tail-risk index measuring demand for out-of-the-money put options. Higher SKEW = more tail-risk hedging.",
        "healthy": "SKEW < 110, indicating complacency; lower hedging demand.",
        "watch": "SKEW 110–120, showing rising tail-risk concerns.",
        "chaos": "SKEW > 120, indicating extreme tail-risk hedging demand and panic.",
        "implications": {
            "short_term": "Rising SKEW often precedes volatility spikes; markets repricing tail risks.",
            "long_term": "Elevated SKEW reflects underlying fragility.",
            "bullish_threshold": "SKEW drops below 105, easing tail-risk hedging pressure.",
            "bearish_threshold": "SKEW exceeds 125, matching pre-crash warning signals.",
        },
        "typical_ranges": {
            "normal": "100–115",
            "stress": "120–135",
            "extreme": "140+ (rare panic levels)",
        },
    },
    "nfci": {
        "label": "NFCI",
        "unit": "std dev",
        "weight": 0.8,
        "description": "National Financial Conditions Index measuring credit, equity, and funding conditions. Positive = stress.",
        "healthy": "NFCI < 0.5, indicating loose financial conditions.",
        "watch": "NFCI 0.5–1.0, showing tightening but manageable.",
        "chaos": "NFCI > 1.0, indicating significant financial stress.",
        "implications": {
            "short_term": "Rising NFCI tightens credit for borrowers; equities weaken.",
            "long_term": "Persistently high NFCI precedes recessions.",
            "bullish_threshold": "NFCI drops below 0.5, easing credit stress.",
            "bearish_threshold": "NFCI exceeds 1.2, matching recession warning levels.",
        },
        "typical_ranges": {
            "normal": "-0.5 to +0.5",
            "stress": "+0.8 to +1.5",
            "extreme": "+2.0+ (severe stress)",
        },
    },
    "vvix": {
        "label": "VVIX",
        "unit": "index",
        "weight": 0.7,
        "description": "Volatility of VIX itself. Rising VVIX = VIX becoming more unstable, often signaling macro uncertainty.",
        "healthy": "VVIX < 70, indicating stable volatility regime.",
        "watch": "VVIX 70–85, showing elevated volatility of volatility.",
        "chaos": "VVIX > 85, indicating extreme VIX regime change.",
        "implications": {
            "short_term": "High VVIX precedes sharp VIX moves and equity whipsaws.",
            "long_term": "Sustained high VVIX suggests broken price discovery.",
            "bullish_threshold": "VVIX drops below 65, stabilizing the volatility regime.",
            "bearish_threshold": "VVIX exceeds 90, often accompanying flash crashes.",
        },
        "typical_ranges": {
            "normal": "50–70",
            "stress": "80–100",
            "extreme": "110+ (extreme dislocation)",
        },
    },
    "air_pocket_risk": {
        "label": "Air Pocket Risk",
        "unit": "%",
        "weight": 0.8,
        "description": "Probability of sudden large drawdown (5%+ intraday drop) due to liquidity evaporation.",
        "healthy": "Air pocket risk < 10%, low probability of sudden drops.",
        "watch": "Air pocket risk 10–20%, meaningful risk of gaps.",
        "chaos": "Air pocket risk > 20%, high odds of flash-crash-like moves.",
        "implications": {
            "short_term": "Rising air pocket risk triggers wide bid-ask spreads and stop-loss cascades.",
            "long_term": "Structural air pocket risk reflects low market resilience.",
            "bullish_threshold": "Air pocket risk drops below 8%, showing market healing.",
            "bearish_threshold": "Air pocket risk exceeds 25%, matching pre-crash vulnerability.",
        },
        "typical_ranges": {
            "normal": "5–12%",
            "stress": "15–25%",
            "extreme": "30%+ (crash imminent)",
        },
    },
    "vix": {
        "label": "VIX",
        "unit": "index",
        "weight": 1.0,
        "description": "Equity volatility index (implied volatility from S&P 500 options). Core market fear gauge.",
        "healthy": "VIX < 15, indicating low implied equity volatility and complacency.",
        "watch": "VIX 15–25, showing elevated caution.",
        "chaos": "VIX > 25, indicating panic selling and crisis conditions.",
        "implications": {
            "short_term": "VIX spikes often trigger cascading liquidations and short squeezes.",
            "long_term": "Sustained elevated VIX reflects growth concerns or policy uncertainty.",
            "bullish_threshold": "VIX drops below 14 from higher levels, signaling sentiment recovery.",
            "bearish_threshold": "VIX exceeds 35, matching 2008/2020 crash conditions.",
        },
        "typical_ranges": {
            "normal": "12–18",
            "stress": "25–40",
            "extreme": "50+ (rare panic)",
        },
    },
    "gold": {
        "label": "Gold",
        "unit": "$/oz",
        "weight": 0.6,
        "description": "Gold prices. Rises during risk-off and geopolitical stress; falls during risk-on.",
        "healthy": "Gold flat to declining (< +2% YoY), indicating strong risk appetite.",
        "watch": "Gold moderately strong (+2–5% YoY), showing flight-to-safety.",
        "chaos": "Gold surging (> +5% YoY), reflecting acute geopolitical/inflation stress.",
        "implications": {
            "short_term": "Gold spikes often accompany equity selloffs and policy shocks.",
            "long_term": "Rising gold trends reflect inflation fears or loss of confidence in fiat.",
            "bullish_threshold": "Gold peaks and rolls over, showing crisis is passing.",
            "bearish_threshold": "Gold exceeds prior crisis highs (e.g., 2011 peak), indicating new stress regime.",
        },
        "typical_ranges": {
            "normal": "$1,600–$1,900/oz",
            "stress": "$2,000–$2,300/oz",
            "extreme": "$2,500+/oz (geopolitical crisis)",
        },
    },
    "oil": {
        "label": "Oil",
        "unit": "$/bbl",
        "weight": 0.6,
        "description": "Crude oil prices. Sensitive to growth, geopolitical risk, and OPEC policy.",
        "healthy": "Oil prices stable or declining (< 3% change/month), supporting growth.",
        "watch": "Oil moderately volatile (+/- 5%/month), showing supply/demand tension.",
        "chaos": "Oil surging or crashing (> 10%/month), reflecting shocks.",
        "implications": {
            "short_term": "Oil spikes can trigger inflation expectations and consumer pain.",
            "long_term": "Sustained high oil pressures inflation and GDP growth.",
            "bullish_threshold": "Oil moderates after spike, easing inflation fears.",
            "bearish_threshold": "Oil exceeds $120/bbl, risking stagflationary shock.",
        },
        "typical_ranges": {
            "normal": "$60–$90/bbl",
            "stress": "$100–$130/bbl",
            "extreme": "$150+/bbl (geopolitical crisis)",
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
    # Count states
    healthy_count = sum(1 for s in states.values() if s == 1)
    watch_count = sum(1 for s in states.values() if s == 2)
    chaos_count = sum(1 for s in states.values() if s == 3)
    total_count = len(states)

    # Map score_level to health
    health_map = {
        "bullish": "Bullish",
        "neutral": "Neutral",
        "bearish": "Bearish",
    }
    health = health_map.get(score_level, "Unknown")

    # Short-term outlook
    if chaos_count > 3:
        short_term_dir = "Bearish"
        short_term_reasoning = "Multiple indicators in chaos; expect downside risk."
        short_term_horizon = "1-4 weeks"
    elif watch_count > 4:
        short_term_dir = "Cautious"
        short_term_reasoning = "Mixed signals with elevated caution; downside bias."
        short_term_horizon = "1-4 weeks"
    elif healthy_count >= total_count - 2:
        short_term_dir = "Bullish"
        short_term_reasoning = "Most indicators healthy; positive momentum expected."
        short_term_horizon = "1-4 weeks"
    else:
        short_term_dir = "Neutral"
        short_term_reasoning = "Balanced signals; direction unclear."
        short_term_horizon = "1-4 weeks"

    # Long-term outlook
    if chaos_count > 2 and watch_count > 3:
        long_term_dir = "Bearish"
        long_term_reasoning = "Accumulating stress indicators suggest longer-term headwinds."
        long_term_horizon = "3-12 months"
    elif healthy_count < 4:
        long_term_dir = "Cautious"
        long_term_reasoning = "Fragility building; risk of deterioration over months."
        long_term_horizon = "3-12 months"
    elif healthy_count >= total_count - 2:
        long_term_dir = "Bullish"
        long_term_reasoning = "Strong fundamentals suggest sustained upside bias."
        long_term_horizon = "3-12 months"
    else:
        long_term_dir = "Neutral"
        long_term_reasoning = "Mixed signals; no clear multi-month trend."
        long_term_horizon = "3-12 months"

    # Top risks (indicators in chaos or watch)
    top_risks = []
    for key, state in states.items():
        if state in [2, 3]:
            meta = get_indicator_info(key)
            if meta:
                label = meta.get("label", key)
                if state == 3:
                    top_risks.append(f"{label} in chaos state")
                else:
                    top_risks.append(f"{label} elevated risk")
    top_risks = top_risks[:3]  # Top 3

    # Opportunities (indicators in healthy)
    opportunities = []
    if healthy_count > 6:
        opportunities.append("Broad-based indicator health supports constructive positioning")
    if "vix" in indicators and states.get("vix") == 1:
        opportunities.append("Low volatility provides entry opportunity window")
    if "hy_credit_spreads" in indicators and states.get("hy_credit_spreads") == 1:
        opportunities.append("Tight spreads indicate strong credit demand")

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
