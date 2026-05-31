"""Plain data structures passed between the data layer, scorers, and the UI.

Using lightweight dataclasses keeps the boundaries explicit and makes the scoring
functions easy to unit-test with hand-built fixtures (no live network needed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .config import Rating


@dataclass
class StockData:
    """Raw data fetched for a single ticker.

    Fields may be empty/None when ``yfinance`` doesn't return them; each scorer is
    responsible for degrading gracefully (falling back to a neutral score).
    """

    ticker: str

    # Daily OHLCV history (index = date). Columns include at least 'Close'.
    price_history: pd.DataFrame = field(default_factory=pd.DataFrame)

    # Current/most-recent price.
    current_price: float | None = None

    # Key/value snapshot from yfinance's ``.info`` (P/E, market cap, etc.).
    info: dict[str, Any] = field(default_factory=dict)

    # Annual financial statements (index = line item, columns = periods).
    income_statement: pd.DataFrame = field(default_factory=pd.DataFrame)
    balance_sheet: pd.DataFrame = field(default_factory=pd.DataFrame)
    cash_flow: pd.DataFrame = field(default_factory=pd.DataFrame)

    # Analyst signals.
    recommendation_mean: float | None = None  # yfinance scale (1=Strong Buy .. 5=Strong Sell)
    target_mean_price: float | None = None

    def has_price_history(self) -> bool:
        return not self.price_history.empty and "Close" in self.price_history.columns


@dataclass
class ComponentScores:
    """The three sub-scores, each on the 1–5 scale."""

    fundamental: float
    technical: float
    analyst: float


@dataclass
class RatingResult:
    """Final output returned by the engine and rendered by the UI."""

    ticker: str
    composite: float
    rating: Rating
    components: ComponentScores
    # Free-form human-readable notes per component (e.g. "F-Score 7/9", "RSI 28 oversold").
    explanations: dict[str, str] = field(default_factory=dict)
    # Set when data was missing/partial so the UI can warn the user.
    warnings: list[str] = field(default_factory=list)
