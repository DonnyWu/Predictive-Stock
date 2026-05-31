"""Technical scorer — EMA crossover + RSI(14) blended into a [1, 5] sub-score.

Both indicators are computed from the price history in StockData.
Falls back to SCORE_NEUTRAL when there is insufficient history.
"""
from __future__ import annotations

import logging

import pandas as pd

from .config import (
    EMA_LONG_WINDOW,
    EMA_SHORT_WINDOW,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    RSI_WINDOW,
    SCORE_MAX,
    SCORE_MIN,
    SCORE_NEUTRAL,
)
from .models import StockData

logger = logging.getLogger(__name__)


def _clamp(v: float) -> float:
    return max(SCORE_MIN, min(SCORE_MAX, v))


def _ema_score(closes: pd.Series, short: int, long: int) -> tuple[float, str]:
    if len(closes) < long:
        return SCORE_NEUTRAL, f"Need ≥{long} bars for EMA{long} (have {len(closes)})"

    ema_short = float(closes.ewm(span=short, adjust=False).mean().iloc[-1])
    ema_long = float(closes.ewm(span=long, adjust=False).mean().iloc[-1])

    if ema_long == 0:
        return SCORE_NEUTRAL, "EMA long is zero"

    gap_pct = (ema_short - ema_long) / abs(ema_long) * 100
    direction = "above" if gap_pct >= 0 else "below"
    note = f"EMA{short} {abs(gap_pct):.1f}% {direction} EMA{long}"

    if gap_pct > 10:
        return 5.0, note
    if gap_pct > 5:
        return 4.0, note
    if gap_pct > 0:
        return 3.5, note
    if gap_pct > -5:
        return 2.5, note
    if gap_pct > -10:
        return 2.0, note
    return 1.0, note


def _rsi_score(closes: pd.Series, window: int) -> tuple[float, str]:
    if len(closes) < window + 1:
        return SCORE_NEUTRAL, f"Need ≥{window + 1} bars for RSI{window}"

    delta = closes.diff()
    avg_gain = delta.clip(lower=0).ewm(com=window - 1, adjust=False).mean()
    avg_loss = (-delta).clip(lower=0).ewm(com=window - 1, adjust=False).mean()

    last_loss = float(avg_loss.iloc[-1])
    last_gain = float(avg_gain.iloc[-1])

    if last_loss == 0:
        rsi = 100.0
    else:
        rsi = 100.0 - 100.0 / (1.0 + last_gain / last_loss)

    if rsi < RSI_OVERSOLD:
        return 4.5, f"RSI {rsi:.0f} (oversold)"
    if rsi < 45:
        return 3.5, f"RSI {rsi:.0f}"
    if rsi < 55:
        return 3.0, f"RSI {rsi:.0f} (neutral)"
    if rsi < RSI_OVERBOUGHT:
        return 2.5, f"RSI {rsi:.0f}"
    return 1.5, f"RSI {rsi:.0f} (overbought)"


def score(data: StockData) -> tuple[float, str]:
    """Return the technical sub-score in [1.0, 5.0] and a brief explanation."""
    if not data.has_price_history():
        return SCORE_NEUTRAL, "No price history available"

    closes = data.price_history["Close"].dropna()
    if len(closes) < 2:
        return SCORE_NEUTRAL, "Insufficient price data"

    ema_s, ema_note = _ema_score(closes, EMA_SHORT_WINDOW, EMA_LONG_WINDOW)
    rsi_s, rsi_note = _rsi_score(closes, RSI_WINDOW)

    blended = _clamp(0.5 * ema_s + 0.5 * rsi_s)
    return blended, f"{ema_note}; {rsi_note}"
