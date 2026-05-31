"""Central configuration for the rating model.

Everything tunable lives here — weights, rating thresholds, and indicator windows —
so the scoring logic in the other modules stays free of magic numbers.
"""

from __future__ import annotations

from enum import Enum

# --------------------------------------------------------------------------- #
# Component weights (must sum to 1.0)
# --------------------------------------------------------------------------- #
WEIGHT_FUNDAMENTAL: float = 0.40
WEIGHT_TECHNICAL: float = 0.35
WEIGHT_ANALYST: float = 0.25

assert abs(WEIGHT_FUNDAMENTAL + WEIGHT_TECHNICAL + WEIGHT_ANALYST - 1.0) < 1e-9, (
    "Component weights must sum to 1.0"
)

# --------------------------------------------------------------------------- #
# Score scale
# --------------------------------------------------------------------------- #
# Every component produces a sub-score on this scale, and so does the composite.
SCORE_MIN: float = 1.0
SCORE_MAX: float = 5.0
SCORE_NEUTRAL: float = 3.0  # used as a graceful fallback when a signal can't be computed


# --------------------------------------------------------------------------- #
# Rating buckets
# --------------------------------------------------------------------------- #
class Rating(str, Enum):
    """Final classification labels."""

    STRONG_BUY = "Strong Buy"
    MODERATE_BUY = "Moderate Buy"
    HOLD = "Hold"
    SELL = "Sell"


# Lower-bound thresholds (a composite >= threshold earns that rating).
# Checked from highest to lowest; anything below the last falls through to SELL.
RATING_THRESHOLDS: list[tuple[float, Rating]] = [
    (4.5, Rating.STRONG_BUY),
    (3.5, Rating.MODERATE_BUY),
    (2.5, Rating.HOLD),
    # < 2.5 -> Rating.SELL
]


def classify(composite: float) -> Rating:
    """Map a composite score in [1, 5] to a :class:`Rating`."""
    for threshold, rating in RATING_THRESHOLDS:
        if composite >= threshold:
            return rating
    return Rating.SELL


# --------------------------------------------------------------------------- #
# Technical-analysis windows
# --------------------------------------------------------------------------- #
EMA_SHORT_WINDOW: int = 50
EMA_LONG_WINDOW: int = 200
RSI_WINDOW: int = 14

# RSI reversion thresholds
RSI_OVERSOLD: float = 30.0   # below -> bullish (potential rebound)
RSI_OVERBOUGHT: float = 70.0  # above -> bearish

# Amount of daily price history to request (must comfortably exceed EMA_LONG_WINDOW).
PRICE_HISTORY_PERIOD: str = "2y"

# --------------------------------------------------------------------------- #
# Fundamental blend (within the 40% fundamental bucket)
# --------------------------------------------------------------------------- #
PIOTROSKI_BLEND: float = 0.60  # weight of Piotroski F-Score vs. valuation check
VALUATION_BLEND: float = 0.40
