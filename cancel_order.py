import os

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus


ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    raise RuntimeError("Alpaca API keys are missing.")


trading_client = TradingClient(
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
    paper=True
)


print("=" * 60)
print("CANCEL AAPL TEST ORDER")
print("=" * 60)


# Find all open AAPL orders
request = GetOrdersRequest(
    status=QueryOrderStatus.OPEN,
    symbols=["AAPL"]
)

orders = trading_client.get_orders(filter=request)


if not orders:
    print()
    print("No open AAPL orders found.")
    print("Nothing to cancel.")
    raise SystemExit


print()
print(f"Found {len(orders)} open AAPL order(s):")


for order in orders:
    print()
    print(f"Order ID: {order.id}")
    print(f"Symbol:   {order.symbol}")
    print(f"Side:     {order.side}")
    print(f"Status:   {order.status}")
    print(f"Notional: {order.notional}")


print()
print("Cancelling the open AAPL order(s)...")


for order in orders:
    trading_client.cancel_order_by_id(order.id)

    print()
    print(f"Cancellation requested: {order.id}")


print()
print("=" * 60)
print("CANCELLATION COMPLETE")
print("=" * 60)