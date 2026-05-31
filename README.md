# Predictive-Stock

A simple stock rating app: enter a ticker (e.g. `AAPL`, `NVDA`) and get a rating —
**Strong Buy / Moderate Buy / Hold / Sell** — with a breakdown of why.

The rating is a transparent, deterministic weighted score of three signals, each normalized to a
common **1.0–5.0** scale and blended by fixed weights:

| Weight | Signal                                   |
|--------|------------------------------------------|
| 40%    | Fundamental (Piotroski F-Score + value)  |
| 35%    | Technical (EMA crossover + RSI)          |
| 25%    | Analyst consensus (recommendations)      |

```
composite = 0.40*fundamental + 0.35*technical + 0.25*analyst
```

| Composite score | Rating       |
|-----------------|--------------|
| ≥ 4.5           | Strong Buy   |
| 3.5 – 4.4       | Moderate Buy |
| 2.5 – 3.4       | Hold         |
| < 2.5           | Sell         |

All data comes from [`yfinance`](https://pypi.org/project/yfinance/) — **free, no API key, no
signup**.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Test

```bash
pytest
```

## ⚠️ Disclaimer

This app produces an **algorithmic score for educational/informational purposes only**. It is
**not investment advice**. Do your own research before making any financial decision.

---

### Project layout

```
Predictive-Stock/
├── app.py                 # Streamlit UI (entry point)
├── requirements.txt
└── stockrater/            # all scoring logic (no UI deps)
    ├── config.py          # weights, thresholds, EMA/RSI windows, Rating enum
    ├── models.py          # data structures
    ├── data.py            # yfinance data fetching
    ├── fundamental.py     # fundamental sub-score (1–5)
    ├── technical.py       # technical sub-score (1–5)
    ├── analyst.py         # analyst sub-score (1–5)
    └── engine.py          # orchestrates everything -> RatingResult
```

> **Status:** Phase 1 complete — environment + data layer (`config.py`, `models.py`, `data.py`).
> Scoring modules, engine, and UI come in later phases.
