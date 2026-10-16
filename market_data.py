import os
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

request = StockLatestTradeRequest(
    symbol_or_symbols="AAPL"
)

trade = client.get_stock_latest_trade(request)

print("AAPL latest price:", trade["AAPL"].price)