import os
from datetime import datetime, timedelta, timezone

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

end = datetime.now(timezone.utc)
start = end - timedelta(days=365)

request = StockBarsRequest(
    symbol_or_symbols="AAPL",
    timeframe=TimeFrame.Day,
    start=start,
    end=end,
    feed=DataFeed.IEX
)

bars = client.get_stock_bars(request)

for bar in bars["AAPL"][-10:]:
    print(
        bar.timestamp.date(),
        "Open:", bar.open,
        "High:", bar.high,
        "Low:", bar.low,
        "Close:", bar.close,
        "Volume:", bar.volume
    )