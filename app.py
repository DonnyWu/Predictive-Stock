"""Streamlit UI — run with: streamlit run app.py"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from stockrater.config import Rating
from stockrater.data import TickerNotFoundError
from stockrater.engine import analyze

st.set_page_config(page_title="Stock Rater", page_icon="📈", layout="centered")
st.title("📈 Stock Rater")
st.caption(
    "Enter a ticker to get an algorithmic rating based on fundamentals, "
    "technicals, and analyst consensus."
)

# ---- Input -------------------------------------------------------------------
col_in, col_btn = st.columns([3, 1])
with col_in:
    raw = st.text_input("Ticker", placeholder="e.g. AAPL, MSFT, NVDA", label_visibility="collapsed")
with col_btn:
    run = st.button("Rate", type="primary", use_container_width=True)

ticker = raw.strip().upper()

st.caption(
    "⚠️ **Disclaimer:** Algorithmic score for educational/informational use only — "
    "**not investment advice**. Always do your own research."
)

# ---- Analysis ----------------------------------------------------------------
if run and not ticker:
    st.warning("Please enter a ticker symbol.")
    st.stop()

if run and ticker:
    with st.spinner(f"Fetching and scoring {ticker}…"):
        try:
            result = analyze(ticker)
        except TickerNotFoundError as exc:
            st.error(f"Ticker not found: {exc}")
            st.stop()
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")
            st.stop()

    BADGE = {
        Rating.STRONG_BUY: "🟢",
        Rating.MODERATE_BUY: "🟡",
        Rating.HOLD: "🟠",
        Rating.SELL: "🔴",
    }

    st.markdown("---")
    st.markdown(f"## {BADGE[result.rating]} **{result.ticker}** — {result.rating.value}")
    st.metric("Composite Score", f"{result.composite:.2f} / 5.00", help="Weighted average of all three signals (1 = worst, 5 = best)")

    st.markdown("### Component Breakdown")
    c1, c2, c3 = st.columns(3)

    def _render_component(col, label: str, weight: str, s: float, note: str) -> None:
        with col:
            st.metric(label, f"{s:.2f}", help=f"Weight: {weight}")
            st.progress((s - 1.0) / 4.0)
            st.caption(note)

    _render_component(c1, "Fundamental", "40%", result.components.fundamental, result.explanations.get("Fundamental", ""))
    _render_component(c2, "Technical", "35%", result.components.technical, result.explanations.get("Technical", ""))
    _render_component(c3, "Analyst", "25%", result.components.analyst, result.explanations.get("Analyst", ""))

    # Score breakdown bar chart
    st.markdown("### Score Chart")
    chart_df = pd.DataFrame(
        {
            "Score": [
                result.components.fundamental,
                result.components.technical,
                result.components.analyst,
            ]
        },
        index=["Fundamental (40%)", "Technical (35%)", "Analyst (25%)"],
    )
    st.bar_chart(chart_df)

    for warning in result.warnings:
        st.warning(warning)
