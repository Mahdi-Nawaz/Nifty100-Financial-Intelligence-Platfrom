import sqlite3
import pandas as pd

conn = sqlite3.connect("data/nifty100.db")
print("Stock prices sample:")
print(pd.read_sql_query("SELECT * FROM stock_prices LIMIT 5", conn))

print("\nDate range in stock_prices:")
print(pd.read_sql_query("SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(DISTINCT date) as num_dates FROM stock_prices", conn))

print("\nMarket cap sample:")
print(pd.read_sql_query("SELECT * FROM market_cap LIMIT 5", conn))

print("\nYears in market_cap:")
print(pd.read_sql_query("SELECT DISTINCT year FROM market_cap ORDER BY year", conn))

print("\nYears in financial_ratios:")
print(pd.read_sql_query("SELECT DISTINCT year FROM financial_ratios ORDER BY year", conn))
