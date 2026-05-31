"""Engine tests — verify weighting math and rating-boundary mapping.

All three scorers and the data layer are mocked so there are no live network calls.
"""
from __future__ import annotations

from unittest.mock import patch

from stockrater.config import Rating
from stockrater.engine import analyze
from stockrater.models import RatingResult, StockData


def _run(fund: float, tech: float, anal: float) -> RatingResult:
    dummy = StockData(ticker="TEST")
    with (
        patch("stockrater.engine.fetch_stock_data", return_value=dummy),
        patch("stockrater.fundamental.score", return_value=(fund, "mock")),
        patch("stockrater.technical.score", return_value=(tech, "mock")),
        patch("stockrater.analyst.score", return_value=(anal, "mock")),
    ):
        return analyze("TEST")


# ---- boundary tests ----------------------------------------------------------

def test_strong_buy_at_4_5():
    r = _run(4.5, 4.5, 4.5)
    assert r.composite == 4.5
    assert r.rating == Rating.STRONG_BUY


def test_just_below_strong_buy():
    r = _run(4.4, 4.4, 4.4)
    assert r.rating == Rating.MODERATE_BUY


def test_moderate_buy_at_3_5():
    r = _run(3.5, 3.5, 3.5)
    assert r.composite == 3.5
    assert r.rating == Rating.MODERATE_BUY


def test_hold_at_2_5():
    r = _run(2.5, 2.5, 2.5)
    assert r.composite == 2.5
    assert r.rating == Rating.HOLD


def test_sell_below_2_5():
    r = _run(2.4, 2.4, 2.4)
    assert r.rating == Rating.SELL


# ---- weighting test ----------------------------------------------------------

def test_weighting_math():
    # 0.40*5 + 0.35*1 + 0.25*3 = 2.0 + 0.35 + 0.75 = 3.10
    r = _run(5.0, 1.0, 3.0)
    assert abs(r.composite - 3.10) < 0.001
    assert r.rating == Rating.HOLD


# ---- result shape ------------------------------------------------------------

def test_result_fields_populated():
    r = _run(3.0, 3.0, 3.0)
    assert r.ticker == "TEST"
    assert 1.0 <= r.composite <= 5.0
    assert r.components.fundamental == 3.0
    assert r.components.technical == 3.0
    assert r.components.analyst == 3.0
    assert "Fundamental" in r.explanations
