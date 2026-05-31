import numpy as np
import pandas as pd
import pytest

from stockrater.technical import score, _ema_score, _rsi_score
from stockrater.config import (
    EMA_LONG_WINDOW,
    EMA_SHORT_WINDOW,
    RSI_WINDOW,
    SCORE_MIN,
    SCORE_MAX,
    SCORE_NEUTRAL,
)
from stockrater.models import StockData


def _price_df(arr) -> pd.DataFrame:
    return pd.DataFrame({"Close": arr})


def test_uptrend_ema_scores_high():
    prices = pd.Series(100.0 * (1 + np.arange(300) * 0.003))
    s, _ = _ema_score(prices, EMA_SHORT_WINDOW, EMA_LONG_WINDOW)
    assert s >= 3.5


def test_downtrend_ema_scores_low():
    prices = pd.Series(np.linspace(200.0, 50.0, 300))
    s, _ = _ema_score(prices, EMA_SHORT_WINDOW, EMA_LONG_WINDOW)
    assert s <= 2.5


def test_insufficient_bars_returns_neutral():
    prices = pd.Series([100.0] * 50)
    s, _ = _ema_score(prices, EMA_SHORT_WINDOW, EMA_LONG_WINDOW)
    assert s == SCORE_NEUTRAL


def test_rsi_oversold():
    prices = [100.0]
    for _ in range(250):
        prices.append(prices[-1] * 1.001)
    for _ in range(30):
        prices.append(prices[-1] * 0.97)
    s, note = _rsi_score(pd.Series(prices), RSI_WINDOW)
    assert s >= 4.0
    assert "oversold" in note.lower()


def test_rsi_overbought():
    prices = [50.0]
    for _ in range(250):
        prices.append(prices[-1] * 0.999)
    for _ in range(30):
        prices.append(prices[-1] * 1.04)
    s, note = _rsi_score(pd.Series(prices), RSI_WINDOW)
    assert s <= 2.0
    assert "overbought" in note.lower()


def test_no_price_history_returns_neutral():
    s, _ = score(StockData(ticker="T"))
    assert s == SCORE_NEUTRAL


def test_score_clamped():
    prices = 100.0 * (1 + np.arange(300) * 0.003)
    s, _ = score(StockData(ticker="T", price_history=_price_df(prices)))
    assert SCORE_MIN <= s <= SCORE_MAX
