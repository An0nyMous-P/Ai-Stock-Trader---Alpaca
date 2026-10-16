import os

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus


API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("Alpaca API keys are missing.")

trading_client = TradingClient(
    API_KEY,
    SECRET_KEY,
    paper=True
)


print("=" * 60)
print("LATEST PAPER ORDER STATUS")
print("=" * 60)


# Get recent orders
request = GetOrdersRequest(
    status=QueryOrderStatus.ALL,
    limit=10
)

orders = trading_client.get_orders(filter=request)


if not orders:
    print()
    print("No orders found.")
    raise SystemExit


# Alpaca returns newest orders first in normal usage.
order = orders[0]


print()
print("Order ID:", order.id)
print("Symbol:", order.symbol)
print("Side:", order.side)
print("Status:", order.status)
print("Notional:", order.notional)
print("Quantity:", order.qty)
print("Filled quantity:", order.filled_qty)
print("Filled average price:", order.filled_avg_price)


print()
print("=" * 60)
print("CURRENT PAPER ACCOUNT")
print("=" * 60)


account = trading_client.get_account()

print()
print(f"Cash: ${float(account.cash):,.2f}")
print(f"Portfolio value: ${float(account.portfolio_value):,.2f}")
print(f"Buying power: ${float(account.buying_power):,.2f}")


print()
print("=" * 60)
print(f"{order.symbol} POSITION")
print("=" * 60)


positions = trading_client.get_all_positions()

position = None

for p in positions:
    if p.symbol == order.symbol:
        position = p
        break


if position:
    print()
    print("Shares:", position.qty)
    print("Market value:", position.market_value)
    print("Unrealized P/L:", position.unrealized_pl)
    print("Average entry price:", position.avg_entry_price)

else:
    print()
    print(f"No {order.symbol} position currently held.")


print()
print("=" * 60)

if str(order.status) == "OrderStatus.FILLED":
    print("ORDER IS FILLED")
elif str(order.status) in [
    "OrderStatus.ACCEPTED",
    "OrderStatus.NEW",
    "OrderStatus.PENDING_NEW"
]:
    print("ORDER IS STILL OPEN / PROCESSING")
else:
    print("ORDER STATUS:", order.status)

print("=" * 60)