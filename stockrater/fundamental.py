"""Fundamental scorer — Piotroski F-Score blended with a simple P/E valuation check.

Returns a sub-score in [1.0, 5.0]. Falls back to SCORE_NEUTRAL when key data is absent.
"""
from __future__ import annotations

import logging

import pandas as pd

from .config import PIOTROSKI_BLEND, SCORE_MAX, SCORE_MIN, SCORE_NEUTRAL, VALUATION_BLEND
from .models import StockData

logger = logging.getLogger(__name__)


def _clamp(v: float) -> float:
    return max(SCORE_MIN, min(SCORE_MAX, v))


def _get(df: pd.DataFrame, *keys: str, col: int = 0) -> float | None:
    """Return the first matching row value at column index *col*, or None."""
    for key in keys:
        if key in df.index:
            try:
                val = df.loc[key].iloc[col]
                if pd.notna(val):
                    return float(val)
            except Exception:
                pass
    return None


def _piotroski(data: StockData) -> tuple[float, str]:
    """Compute a Piotroski F-Score and normalise it to [1, 5]."""
    inc = data.income_statement
    bal = data.balance_sheet
    cf = data.cash_flow

    if inc.empty and bal.empty:
        return SCORE_NEUTRAL, "No financial statement data"

    bits: list[int] = []
    notes: list[str] = []

    total_assets = _get(bal, "Total Assets")
    net_income = _get(inc, "Net Income")
    op_cf = _get(cf, "Operating Cash Flow")

    # Signal 1: ROA > 0
    if total_assets and net_income is not None:
        roa = net_income / total_assets
        bits.append(1 if roa > 0 else 0)
        notes.append(f"ROA {roa:.1%}")

    # Signal 2: Operating cash flow > 0
    if op_cf is not None:
        bits.append(1 if op_cf > 0 else 0)

    # Signal 3: Cash earnings quality (OCF/Assets > ROA)
    if total_assets and net_income is not None and op_cf is not None:
        bits.append(1 if (op_cf / total_assets) > (net_income / total_assets) else 0)

    has_two = (not inc.empty and len(inc.columns) >= 2) or (
        not bal.empty and len(bal.columns) >= 2
    )
    if has_two:
        total_assets_p = _get(bal, "Total Assets", col=1)
        net_income_p = _get(inc, "Net Income", col=1)
        rev = _get(inc, "Total Revenue")
        rev_p = _get(inc, "Total Revenue", col=1)
        gp = _get(inc, "Gross Profit")
        gp_p = _get(inc, "Gross Profit", col=1)
        ltd = _get(bal, "Long Term Debt", "Long-Term Debt")
        ltd_p = _get(bal, "Long Term Debt", "Long-Term Debt", col=1)
        ca = _get(bal, "Current Assets")
        cl = _get(bal, "Current Liabilities")
        ca_p = _get(bal, "Current Assets", col=1)
        cl_p = _get(bal, "Current Liabilities", col=1)
        shares = _get(bal, "Ordinary Shares Number", "Share Issued")
        shares_p = _get(bal, "Ordinary Shares Number", "Share Issued", col=1)

        # Signal 4: ROA improved
        if total_assets and total_assets_p and net_income is not None and net_income_p is not None:
            bits.append(
                1 if (net_income / total_assets) > (net_income_p / total_assets_p) else 0
            )

        # Signal 5: Leverage decreased
        if total_assets and total_assets_p and ltd is not None and ltd_p is not None:
            bits.append(
                1 if (ltd / total_assets) < (ltd_p / total_assets_p) else 0
            )

        # Signal 6: Current ratio improved
        if ca and cl and ca_p and cl_p and cl != 0 and cl_p != 0:
            cr = ca / cl
            bits.append(1 if cr > (ca_p / cl_p) else 0)
            notes.append(f"CR {cr:.2f}")

        # Signal 7: No dilution (allow 2% tolerance)
        if shares and shares_p:
            bits.append(1 if shares <= shares_p * 1.02 else 0)

        # Signal 8: Gross margin improved
        if rev and rev_p and gp is not None and gp_p is not None and rev != 0 and rev_p != 0:
            gm = gp / rev
            bits.append(1 if gm > (gp_p / rev_p) else 0)
            notes.append(f"GM {gm:.1%}")

        # Signal 9: Asset turnover improved
        if rev and rev_p and total_assets and total_assets_p:
            bits.append(
                1 if (rev / total_assets) > (rev_p / total_assets_p) else 0
            )

    if not bits:
        return SCORE_NEUTRAL, "Insufficient financial data"

    f_score = sum(bits)
    max_signals = len(bits)
    scaled = (f_score / max_signals) * 9
    norm_score = 1.0 + (scaled / 9.0) * 4.0

    note_str = f"F-Score {f_score}/{max_signals}"
    if notes:
        note_str += f" ({', '.join(notes)})"
    return _clamp(norm_score), note_str


def _valuation(data: StockData) -> tuple[float, str]:
    """P/E-based valuation check → [1, 5]."""
    pe_raw = data.info.get("trailingPE") or data.info.get("forwardPE")
    try:
        pe = float(pe_raw) if pe_raw is not None else None
        if pe is not None and pe != pe:  # NaN guard
            pe = None
    except (TypeError, ValueError):
        pe = None

    if pe is None or pe <= 0:
        return SCORE_NEUTRAL, "P/E not available"

    if pe < 10:
        return 5.0, f"P/E {pe:.1f} (very cheap)"
    if pe < 15:
        return 4.0, f"P/E {pe:.1f} (cheap)"
    if pe < 25:
        return 3.0, f"P/E {pe:.1f} (fair)"
    if pe < 40:
        return 2.0, f"P/E {pe:.1f} (expensive)"
    return 1.0, f"P/E {pe:.1f} (very expensive)"


def score(data: StockData) -> tuple[float, str]:
    """Return the fundamental sub-score in [1.0, 5.0] and a brief explanation."""
    f_score, f_note = _piotroski(data)
    v_score, v_note = _valuation(data)
    blended = _clamp(PIOTROSKI_BLEND * f_score + VALUATION_BLEND * v_score)
    return blended, f"{f_note}; {v_note}"
