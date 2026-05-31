"""Shared fixtures — no live network calls required."""
from __future__ import annotations

import pandas as pd
import pytest

from stockrater.models import StockData


def _income(**overrides) -> pd.DataFrame:
    data = {
        "2023": {"Total Revenue": 400_000_000, "Gross Profit": 160_000_000, "Net Income": 40_000_000},
        "2022": {"Total Revenue": 350_000_000, "Gross Profit": 133_000_000, "Net Income": 35_000_000},
    }
    for key, val in overrides.items():
        data["2023"][key] = val
    return pd.DataFrame(data)


def _balance(**overrides) -> pd.DataFrame:
    data = {
        "2023": {
            "Total Assets": 500_000_000,
            "Current Assets": 150_000_000,
            "Current Liabilities": 80_000_000,
            "Long Term Debt": 60_000_000,
            "Ordinary Shares Number": 100_000_000,
        },
        "2022": {
            "Total Assets": 470_000_000,
            "Current Assets": 130_000_000,
            "Current Liabilities": 75_000_000,
            "Long Term Debt": 70_000_000,
            "Ordinary Shares Number": 102_000_000,
        },
    }
    for key, val in overrides.items():
        data["2023"][key] = val
    return pd.DataFrame(data)


def _cashflow(**overrides) -> pd.DataFrame:
    data = {
        "2023": {"Operating Cash Flow": 55_000_000},
        "2022": {"Operating Cash Flow": 48_000_000},
    }
    for key, val in overrides.items():
        data["2023"][key] = val
    return pd.DataFrame(data)


@pytest.fixture
def good_stock() -> StockData:
    return StockData(
        ticker="GOOD",
        income_statement=_income(),
        balance_sheet=_balance(),
        cash_flow=_cashflow(),
        info={"trailingPE": 12.0},
        recommendation_mean=1.8,
        target_mean_price=120.0,
        current_price=100.0,
    )


@pytest.fixture
def poor_stock() -> StockData:
    return StockData(
        ticker="POOR",
        income_statement=_income(**{"Net Income": -10_000_000}),
        balance_sheet=_balance(**{"Long Term Debt": 480_000_000}),
        cash_flow=_cashflow(**{"Operating Cash Flow": -5_000_000}),
        info={"trailingPE": 80.0},
        recommendation_mean=4.2,
        target_mean_price=80.0,
        current_price=100.0,
    )


@pytest.fixture
def empty_stock() -> StockData:
    return StockData(ticker="EMPTY")
