from stockrater.analyst import score
from stockrater.config import SCORE_MIN, SCORE_MAX, SCORE_NEUTRAL
from stockrater.models import StockData


def test_strong_buy_recommendation():
    s, _ = score(StockData(ticker="T", recommendation_mean=1.0))
    assert s == 5.0


def test_strong_sell_recommendation():
    s, _ = score(StockData(ticker="T", recommendation_mean=5.0))
    assert s == 1.0


def test_neutral_recommendation():
    s, _ = score(StockData(ticker="T", recommendation_mean=3.0))
    assert 2.8 <= s <= 3.2


def test_no_recommendation_returns_neutral():
    s, _ = score(StockData(ticker="T"))
    assert s == SCORE_NEUTRAL


def test_upside_nudges_score_up():
    s_with = score(StockData(ticker="T", recommendation_mean=3.0, current_price=100.0, target_mean_price=130.0))[0]
    s_base = score(StockData(ticker="T", recommendation_mean=3.0))[0]
    assert s_with > s_base


def test_downside_nudges_score_down():
    s, _ = score(StockData(ticker="T", recommendation_mean=3.0, current_price=100.0, target_mean_price=70.0))
    assert s < 3.0


def test_score_clamped():
    s, _ = score(StockData(ticker="T", recommendation_mean=1.0, current_price=100.0, target_mean_price=999.0))
    assert SCORE_MIN <= s <= SCORE_MAX
