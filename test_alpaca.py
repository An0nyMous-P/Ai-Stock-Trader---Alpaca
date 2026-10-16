from alpaca.trading.client import TradingClient

API_KEY = "PKNXYGP5NVW5FMOP276PWOKFH4"
SECRET_KEY = "4R2uddS6RQKnS8DuMrEjZxHRD48LuqcicatxNqZhC28w"

client = TradingClient(API_KEY, SECRET_KEY, paper=True)

account = client.get_account()

print("Connected to Alpaca!")
print("Cash:", account.cash)
print("Portfolio value:", account.portfolio_value)