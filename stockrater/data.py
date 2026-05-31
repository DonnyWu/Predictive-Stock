"""Data layer — fetches everything we need for one ticker from ``yfinance``.

This is the project's single data source. ``yfinance`` is free and needs no API key,
and it conveniently exposes all three signals we score on:

* price/volume history  -> technical analysis
* financial statements  -> fundamental analysis
* analyst recommendations + target price -> analyst consensus

The public entry point is :func:`fetch_stock_data`, which returns a fully-populated
(or gracefully-degraded) :class:`~stockrater.models.StockData`. Network/parse errors
for individual pieces are caught so a partial fetch never crashes the whole app — the
scorers fall back to a neutral score when a field is missing.
"""

from __future__ import annotations

import logging

import pandas as pd
import yfinance as yf

from .config import PRICE_HISTORY_PERIOD
from .models import StockData

logger = logging.getLogger(__name__)


class TickerNotFoundError(Exception):
    """Raised when a ticker returns no usable data at all (likely invalid symbol)."""


def _safe(label: str, fn):
    """Run ``fn`` and swallow/log any exception, returning ``None`` on failure.

    yfinance is flaky about individual endpoints; we never want one missing piece to
    abort the whole fetch.
    """
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - yfinance raises many ad-hoc error types
        logger.warning("Could not fetch %s: %s", label, exc)
        return None


def _coerce_float(value) -> float | None:
    try:
        if value is None:
            return None
        f = float(value)
        # yfinance sometimes returns NaN floats.
        return f if f == f else None  # NaN != NaN
    except (TypeError, ValueError):
        return None


def fetch_stock_data(ticker: str, *, period: str = PRICE_HISTORY_PERIOD) -> StockData:
    """Fetch all data for ``ticker``.

    Args:
        ticker: Stock symbol, e.g. ``"AAPL"``. Case-insensitive; whitespace stripped.
        period: yfinance history period for price data (default from config).

    Returns:
        A populated :class:`StockData`. Missing pieces are left empty/None.

    Raises:
        ValueError: if ``ticker`` is blank.
        TickerNotFoundError: if no price history *and* no info could be retrieved
            (strong signal the symbol is invalid).
    """
    symbol = (ticker or "").strip().upper()
    if not symbol:
        raise ValueError("Ticker symbol must not be empty.")

    yf_ticker = yf.Ticker(symbol)
    data = StockData(ticker=symbol)

    # --- price/volume history -------------------------------------------------
    history = _safe("price history", lambda: yf_ticker.history(period=period))
    if history is not None and not history.empty:
        data.price_history = history
        data.current_price = _coerce_float(history["Close"].iloc[-1])

    # --- info snapshot (valuation ratios, fallback price/recs) ----------------
    info = _safe("info", lambda: yf_ticker.info) or {}
    if isinstance(info, dict):
        data.info = info
        if data.current_price is None:
            data.current_price = _coerce_float(
                info.get("currentPrice") or info.get("regularMarketPrice")
            )
        data.recommendation_mean = _coerce_float(info.get("recommendationMean"))
        data.target_mean_price = _coerce_float(
            info.get("targetMeanPrice") or info.get("targetMedianPrice")
        )

    # --- financial statements -------------------------------------------------
    income = _safe("income statement", lambda: yf_ticker.income_stmt)
    if isinstance(income, pd.DataFrame):
        data.income_statement = income

    balance = _safe("balance sheet", lambda: yf_ticker.balance_sheet)
    if isinstance(balance, pd.DataFrame):
        data.balance_sheet = balance

    cashflow = _safe("cash flow", lambda: yf_ticker.cashflow)
    if isinstance(cashflow, pd.DataFrame):
        data.cash_flow = cashflow

    # --- validity check -------------------------------------------------------
    if not data.has_price_history() and not data.info:
        raise TickerNotFoundError(
            f"No data found for ticker '{symbol}'. It may be invalid or delisted."
        )

    return data
