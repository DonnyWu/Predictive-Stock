from stockrater.fundamental import score, _piotroski, _valuation
from stockrater.config import SCORE_MIN, SCORE_MAX, SCORE_NEUTRAL
from stockrater.models import StockData


def test_good_stock_scores_high(good_stock):
    s, _ = score(good_stock)
    assert s > 3.5, f"Expected > 3.5, got {s}"


def test_poor_stock_scores_low(poor_stock):
    s, _ = score(poor_stock)
    assert s < 3.0, f"Expected < 3.0, got {s}"


def test_empty_stock_returns_neutral(empty_stock):
    s, _ = score(empty_stock)
    assert s == SCORE_NEUTRAL


def test_score_always_clamped(good_stock, poor_stock):
    for stock in (good_stock, poor_stock):
        s, _ = score(stock)
        assert SCORE_MIN <= s <= SCORE_MAX


def test_valuation_pe_very_cheap():
    d = StockData(ticker="T", info={"trailingPE": 8.0})
    s, note = _valuation(d)
    assert s == 5.0
    assert "cheap" in note.lower()


def test_valuation_pe_very_expensive():
    d = StockData(ticker="T", info={"trailingPE": 55.0})
    s, _ = _valuation(d)
    assert s == 1.0


def test_valuation_pe_fair():
    d = StockData(ticker="T", info={"trailingPE": 20.0})
    s, _ = _valuation(d)
    assert s == 3.0


def test_valuation_no_pe_returns_neutral():
    d = StockData(ticker="T", info={})
    s, _ = _valuation(d)
    assert s == SCORE_NEUTRAL


def test_valuation_negative_pe_returns_neutral():
    d = StockData(ticker="T", info={"trailingPE": -5.0})
    s, _ = _valuation(d)
    assert s == SCORE_NEUTRAL
