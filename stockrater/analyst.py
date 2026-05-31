"""Analyst-consensus scorer.

Maps yfinance's recommendation_mean (1 = Strong Buy, 5 = Strong Sell) onto our
[1, 5] scale by inverting it, then nudges the score by target-price upside.
"""
from __future__ import annotations

import logging

from .config import SCORE_MAX, SCORE_MIN, SCORE_NEUTRAL
from .models import StockData

logger = logging.getLogger(__name__)


def _clamp(v: float) -> float:
    return max(SCORE_MIN, min(SCORE_MAX, v))


def score(data: StockData) -> tuple[float, str]:
    """Return the analyst sub-score in [1.0, 5.0] and a brief explanation."""
    rec = data.recommendation_mean
    if rec is None:
        return SCORE_NEUTRAL, "No analyst recommendations"

    # yfinance: 1=Strong Buy … 5=Strong Sell → invert to our ascending scale
    base = _clamp(6.0 - rec)
    notes = [f"analyst mean {rec:.2f}"]

    nudge = 0.0
    if data.current_price and data.target_mean_price and data.current_price > 0:
        upside = (data.target_mean_price - data.current_price) / data.current_price
        # Max ±0.5 nudge at ±20% upside/downside
        nudge = max(-0.5, min(0.5, upside / 0.20 * 0.5))
        sign = "+" if upside >= 0 else ""
        notes.append(f"target upside {sign}{upside * 100:.0f}%")

    return _clamp(base + nudge), "; ".join(notes)
