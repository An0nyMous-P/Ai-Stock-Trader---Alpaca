import os

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise RuntimeError("Alpaca API keys are missing.")


# HARD SAFETY: PAPER ACCOUNT ONLY
client = TradingClient(
    API_KEY,
    SECRET_KEY,
    paper=True
)


SYMBOL = "JNJ"


print("=" * 60)
print("AUTOMATIC PAPER SELL TEST")
print("=" * 60)


# ------------------------------------------------------------
# FIND JNJ POSITION
# ------------------------------------------------------------

positions = client.get_all_positions()

position = None

for p in positions:
    if p.symbol == SYMBOL:
        position = p
        break


if position is None:
    print()
    print("No JNJ position found.")
    print("Nothing to sell.")
    raise SystemExit


quantity = float(position.qty)


print()
print("Position found:")
print("Symbol:", position.symbol)
print("Shares:", quantity)
print("Market value:", position.market_value)
print("Average entry:", position.avg_entry_price)


# ------------------------------------------------------------
# SAFETY CHECK
# ------------------------------------------------------------

if quantity <= 0:
    raise RuntimeError(
        f"Invalid JNJ quantity: {quantity}"
    )


print()
print("Safety checks:")
print("  ✓ Alpaca PAPER account")
print("  ✓ Live trading is not being used")
print("  ✓ JNJ position exists")
print("  ✓ Position quantity is valid")
print("  ✓ This order cannot create a short position")


# ------------------------------------------------------------
# SUBMIT SELL
# ------------------------------------------------------------

print()
print("Submitting PAPER SELL...")

order = MarketOrderRequest(
    symbol=SYMBOL,
    qty=quantity,
    side=OrderSide.SELL,
    time_in_force=TimeInForce.DAY
)

submitted = client.submit_order(
    order_data=order
)


print()
print("=" * 60)
print("PAPER SELL ORDER SUBMITTED")
print("=" * 60)

print()
print("Order ID:", submitted.id)
print("Symbol:", submitted.symbol)
print("Side:", submitted.side)
print("Quantity:", submitted.qty)
print("Status:", submitted.status)

print()
print("The SELL order was submitted to the PAPER account.")
print("No live money was used.")