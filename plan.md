# Stock Rating App — Implementation Plan

## Context

Build a **simple** app: the user types a stock ticker (e.g. `AAPL`) and gets back one rating —
**Strong Buy / Moderate Buy / Hold / Sell** — plus a short breakdown of why.

The rating is a transparent, deterministic weighted score of three signals (fundamental,
technical, analyst), each normalized to a common **1.0–5.0** scale, then blended by fixed weights.

### Decisions locked in
- **Data — `yfinance` only.** No API key, no signup, 100% free. Provides price/volume history,
  financial statements, AND analyst recommendations + target prices — all three signals from one source.
- **App shape — Streamlit only.** One app, one command to run. No separate FastAPI backend.
- **Scope — single ticker.** Enter one ticker → see the rating + breakdown. No database / watchlist.
- **Testing — pytest** for the deterministic scoring math.
- No API keys → **no `.env`/secrets needed**; config is a plain constants module.
- scikit-learn **dropped** (not needed; normalization is trivial with NumPy). Can add later.

> ⚠️ Output is an algorithmic score for **educational/informational** use only — **not investment
> advice**. A disclaimer is shown in the UI.

---

## Scoring Model

Each signal returns a sub-score in **[1.0, 5.0]**. Composite is their weighted average, so it also
lands in [1.0, 5.0] and maps directly onto the rating buckets.

```
composite = 0.40 * fundamental + 0.35 * technical + 0.25 * analyst
```

| Composite score | Rating       |
|-----------------|--------------|
| ≥ 4.5           | Strong Buy   |
| 3.5 – 4.4       | Moderate Buy |
| 2.5 – 3.4       | Hold         |
| < 2.5           | Sell         |

**1. Fundamental (40%)** — Piotroski F-Score + simple value check
- Piotroski F-Score (0–9) → linear map `1 + (F/9)*4`.
- Simple valuation sanity (P/E, or light DCF/margin-of-safety) → 1–5.
- Blend (default 60% Piotroski / 40% valuation) → fundamental sub-score.

**2. Technical (35%)** — EMA crossover + RSI
- EMA short vs long (default 50/200): bullish separation scores higher.
- RSI(14): <30 oversold (bullish), >70 overbought (bearish), 30–70 neutral.
- Blend → technical sub-score.

**3. Analyst (25%)** — yfinance recommendations
- Map yfinance recommendation mean / counts to a 1–5 score; nudge by target-price upside.
- → analyst sub-score.

All weights, thresholds, and EMA/RSI windows live in `stockrater/config.py` so they're easy to tune.

---

## Project Structure

```
Predictive-Stock/
├── .gitignore
├── README.md
├── PLAN.md                     # this file
├── requirements.txt
├── app.py                      # Streamlit UI — the entry point you run
├── stockrater/
│   ├── __init__.py
│   ├── config.py               # weights 0.40/0.35/0.25, thresholds, EMA/RSI windows, Rating enum
│   ├── models.py               # dataclasses: StockData, ComponentScores, RatingResult
│   ├── data.py                 # yfinance: fetch price/volume, financials, analyst data
│   ├── fundamental.py          # Piotroski + value check -> 1..5
│   ├── technical.py            # EMA crossover + RSI(14) -> 1..5
│   ├── analyst.py              # yfinance recommendations/target -> 1..5
│   └── engine.py               # orchestrate fetch -> 3 scores -> weighted composite -> rating
└── tests/
    ├── conftest.py             # sample/mock data fixtures
    ├── test_fundamental.py
    ├── test_technical.py
    ├── test_analyst.py
    └── test_engine.py          # weighting + threshold boundaries (2.5 / 3.5 / 4.5)
```

**Why this shape:** the `stockrater` package holds all pure logic (no Streamlit imports), so it's
easy to unit-test and `app.py` stays a thin UI layer that just calls `engine.analyze(ticker)`.

---

## Phased Plan

**Phase 1 — Scaffold & data** ✅ *(in progress / done)*
- `requirements.txt`, `.gitignore`, `README.md`, `stockrater/__init__.py`.
- `config.py` (weights, thresholds, windows, `Rating` enum).
- `models.py` (dataclasses for fetched data + results).
- `data.py` (yfinance fetchers; graceful handling of missing fields / bad tickers).

**Phase 2 — Scoring modules + tests**
- `fundamental.py`, `technical.py`, `analyst.py` (each returns a clamped 1–5 sub-score).
- `test_fundamental.py`, `test_technical.py`, `test_analyst.py` with fixed inputs → expected scores.

**Phase 3 — Engine**
- `engine.py`: `analyze(ticker)` fetches data, runs the 3 modules, applies weights, maps to a
  `Rating`, returns a `RatingResult` (composite + per-component breakdown).
- `test_engine.py`: verify weighting + boundary mapping (2.49→Sell, 2.5→Hold, 3.5→Moderate, 4.5→Strong).

**Phase 4 — Streamlit UI**
- `app.py`: ticker input → calls `engine.analyze` → rating badge, composite score, 3-bar component
  breakdown, disclaimer. Loading spinner + friendly error for invalid tickers.
- Finalize `README.md` with run instructions.

---

## File Creation Checklist

- [x] requirements.txt
- [x] .gitignore
- [x] README.md
- [x] stockrater/__init__.py
- [x] stockrater/config.py
- [x] stockrater/models.py
- [x] stockrater/data.py
- [x] stockrater/fundamental.py
- [x] stockrater/technical.py
- [x] stockrater/analyst.py
- [x] stockrater/engine.py
- [x] tests/conftest.py + test_fundamental / test_technical / test_analyst / test_engine
- [x] app.py

---

## Dependencies (`requirements.txt`)

```
streamlit        # the UI / app
yfinance         # free data: price, financials, analyst (no key needed)
pandas, numpy    # data processing + normalization
pytest           # tests
```

---

## How to Run & Verify

- **Install:** `pip install -r requirements.txt`
- **Run the app:** `streamlit run app.py` → enter a ticker → see the rating.
- **Tests:** `pytest` — scoring modules assert exact 1–5 outputs from fixed inputs; `test_engine`
  asserts correct rating at the 2.5 / 3.5 / 4.5 boundaries (no live network in tests).
- **Live sanity check:** run a few well-known tickers (AAPL, NVDA, a weak stock) and confirm the
  ratings are directionally reasonable.

---

## Small choices (sensible defaults; no blockers)
- EMA window pair: default **50/200** (long-term trend); easy to change in `config.py`.
- Valuation method: start with a simple P/E-based check; can upgrade to a light DCF later.
- yfinance occasionally returns missing fields — each module degrades gracefully (neutral 3.0 when a
  signal can't be computed) so the app never crashes on sparse data.
