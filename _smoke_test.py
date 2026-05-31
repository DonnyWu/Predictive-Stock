"""Throwaway Phase 1 smoke test — verifies the data layer against live yfinance.
Safe to delete after Phase 1."""
import logging

logging.disable(logging.CRITICAL)

from stockrater.data import fetch_stock_data, TickerNotFoundError

d = fetch_stock_data("AAPL")
print("ticker         :", d.ticker)
print("price_rows     :", len(d.price_history))
print("current_price  :", round(d.current_price, 2) if d.current_price else None)
print("rec_mean       :", d.recommendation_mean)
print("target_mean    :", d.target_mean_price)
print("income_empty   :", d.income_statement.empty)
print("balance_empty  :", d.balance_sheet.empty)
print("cashflow_empty :", d.cash_flow.empty)
print("info_keys      :", len(d.info))

try:
    fetch_stock_data("ZZZZNOTREAL123")
    print("bad_ticker     : ERROR did not raise")
except TickerNotFoundError:
    print("bad_ticker     : correctly raised TickerNotFoundError")

try:
    fetch_stock_data("")
    print("empty_ticker   : ERROR did not raise")
except ValueError:
    print("empty_ticker   : correctly raised ValueError")

print("SMOKE_TEST_PASSED")
