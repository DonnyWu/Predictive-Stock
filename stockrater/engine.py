"""Orchestrate data fetch → scoring → rating.

Public API: a single :func:`analyze` function that returns a fully-populated
:class:`~stockrater.models.RatingResult`.
"""
from __future__ import annotations

import logging

from . import analyst, fundamental, technical
from .config import WEIGHT_ANALYST, WEIGHT_FUNDAMENTAL, WEIGHT_TECHNICAL, classify
from .data import TickerNotFoundError, fetch_stock_data
from .models import ComponentScores, RatingResult

logger = logging.getLogger(__name__)


def analyze(ticker: str) -> RatingResult:
    """Fetch data for *ticker*, score it, and return a :class:`RatingResult`.

    Raises:
        ValueError: if ticker is blank.
        TickerNotFoundError: if the symbol returns no data.
    """
    data = fetch_stock_data(ticker)

    fund_score, fund_note = fundamental.score(data)
    tech_score, tech_note = technical.score(data)
    anal_score, anal_note = analyst.score(data)

    composite = round(
        WEIGHT_FUNDAMENTAL * fund_score
        + WEIGHT_TECHNICAL * tech_score
        + WEIGHT_ANALYST * anal_score,
        4,
    )
    rating = classify(composite)

    warnings: list[str] = []
    if data.income_statement.empty:
        warnings.append("No income statement — fundamental score may be inaccurate.")
    if not data.has_price_history():
        warnings.append("No price history — technical score unavailable.")
    if data.recommendation_mean is None:
        warnings.append("No analyst recommendations available.")

    return RatingResult(
        ticker=data.ticker,
        composite=composite,
        rating=rating,
        components=ComponentScores(
            fundamental=fund_score,
            technical=tech_score,
            analyst=anal_score,
        ),
        explanations={
            "Fundamental": fund_note,
            "Technical": tech_note,
            "Analyst": anal_note,
        },
        warnings=warnings,
    )
