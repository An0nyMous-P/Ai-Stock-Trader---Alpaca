import os

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    GetOrdersRequest
)
from alpaca.trading.enums import (
    OrderSide,
    TimeInForce,
    QueryOrderStatus
)

from market_hours import get_market_status
from market_config import get_symbols
from trading_config import get_trading_config, TRADING_MODE


# ============================================================
# SETTINGS
# ============================================================

MARKET = "US"

SUPPORTED_STOCKS = get_symbols(MARKET)

CONFIG = get_trading_config()

MAX_POSITION_VALUE = CONFIG.get(
    "max_position_value",
    CONFIG.get("capital_limit", 0.00)
)


# ============================================================
# ALPACA CONNECTION
# ============================================================

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    raise RuntimeError(
        "Alpaca API keys are missing."
    )


# IMPORTANT:
# The current system ONLY connects to Alpaca PAPER.
# Live trading remains disabled.
trading_client = TradingClient(
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
    paper=True
)


# ============================================================
# VALIDATION
# ============================================================

def validate_symbol(symbol):

    symbol = symbol.upper()

    if symbol not in SUPPORTED_STOCKS:
        raise ValueError(
            f"Unsupported stock: {symbol}. "
            f"Allowed stocks: "
            f"{', '.join(SUPPORTED_STOCKS)}"
        )

    return symbol


# ============================================================
# ACCOUNT STATE
# ============================================================

def get_account_state(symbol):

    symbol = validate_symbol(symbol)

    account = trading_client.get_account()

    cash = float(account.cash)
    portfolio_value = float(account.portfolio_value)
    buying_power = float(account.buying_power)

    try:

        position = trading_client.get_open_position(
            symbol
        )

        shares = float(position.qty)
        market_value = float(position.market_value)
        unrealized_pl = float(position.unrealized_pl)

    except Exception:

        shares = 0.0
        market_value = 0.0
        unrealized_pl = 0.0

    return {
        "symbol": symbol,
        "cash": cash,
        "portfolio_value": portfolio_value,
        "buying_power": buying_power,
        "shares": shares,
        "market_value": market_value,
        "unrealized_pl": unrealized_pl
    }


# ============================================================
# ALL POSITIONS
# ============================================================

def get_all_positions():

    positions = trading_client.get_all_positions()

    result = {}

    for position in positions:

        symbol = position.symbol

        result[symbol] = {
            "shares": float(position.qty),
            "market_value": float(position.market_value),
            "unrealized_pl": float(position.unrealized_pl)
        }

    return result


# ============================================================
# OPEN ORDERS
# ============================================================

def get_open_orders(symbol=None):

    if symbol is not None:

        symbol = validate_symbol(symbol)

        request = GetOrdersRequest(
            status=QueryOrderStatus.OPEN,
            symbols=[symbol]
        )

    else:

        request = GetOrdersRequest(
            status=QueryOrderStatus.OPEN
        )

    return trading_client.get_orders(
        filter=request
    )


# ============================================================
# BUY
# ============================================================

def buy_stock(symbol, dollar_amount):

    symbol = validate_symbol(symbol)

    market_status = get_market_status(MARKET)

    if market_status["status"] != "OPEN":

        raise RuntimeError(
            f"Cannot BUY {symbol}: "
            f"market is CLOSED. "
            f"{market_status['reason']}."
        )

    dollar_amount = float(dollar_amount)

    if dollar_amount <= 0:

        raise ValueError(
            "BUY amount must be greater than $0."
        )

    state = get_account_state(symbol)

    if dollar_amount > state["cash"]:

        raise ValueError(
            "BUY amount exceeds available cash."
        )

    if (
        state["market_value"]
        + dollar_amount
        > MAX_POSITION_VALUE
    ):

        raise ValueError(
            f"BUY would exceed the "
            f"${MAX_POSITION_VALUE:.2f} "
            f"maximum position."
        )

    open_orders = get_open_orders(symbol)

    if open_orders:

        raise RuntimeError(
            f"An existing {symbol} order is already open. "
            f"Refusing to create another order."
        )

    # Dollar-based orders allow fractional shares.
    order_data = MarketOrderRequest(
        symbol=symbol,
        notional=round(dollar_amount, 2),
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )

    return trading_client.submit_order(
        order_data=order_data
    )


# ============================================================
# SELL ALL
# ============================================================

def sell_all(symbol):

    symbol = validate_symbol(symbol)

    market_status = get_market_status(MARKET)

    if market_status["status"] != "OPEN":

        raise RuntimeError(
            f"Cannot SELL {symbol}: "
            f"market is CLOSED. "
            f"{market_status['reason']}."
        )

    state = get_account_state(symbol)

    if state["shares"] <= 0:

        raise ValueError(
            f"No {symbol} position exists to sell."
        )

    open_orders = get_open_orders(symbol)

    if open_orders:

        raise RuntimeError(
            f"An existing {symbol} order is already open. "
            f"Refusing to create another order."
        )

    order_data = MarketOrderRequest(
        symbol=symbol,
        qty=state["shares"],
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY
    )

    return trading_client.submit_order(
        order_data=order_data
    )


# ============================================================
# TEST / STATUS
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("US PAPER ORDER ENGINE")
    print("=" * 60)

    print()
    print(
        f"Trading mode: {TRADING_MODE}"
    )

    print(
        f"Supported stocks: "
        f"{len(SUPPORTED_STOCKS)}"
    )

    print(
        f"Maximum position: "
        f"${MAX_POSITION_VALUE:.2f}"
    )

    print(
        f"Fractional shares: "
        f"{CONFIG['fractional_shares']}"
    )

    print(
        f"Leverage: "
        f"{CONFIG['allow_leverage']}"
    )

    print(
        f"Short selling: "
        f"{CONFIG['allow_short_selling']}"
    )

    print()

    market_status = get_market_status(MARKET)

    print(
        f"US market: "
        f"{market_status['status']}"
    )

    print(
        f"Reason: "
        f"{market_status['reason']}"
    )

    print()

    account = trading_client.get_account()

    print(
        f"Actual paper portfolio: "
        f"${float(account.portfolio_value):.2f}"
    )

    print(
        f"Cash: "
        f"${float(account.cash):.2f}"
    )

    print()

    positions = get_all_positions()

    if not positions:

        print("Current positions: None")

    else:

        print("Current positions:")

        for symbol, position in positions.items():

            print(
                f"  {symbol}: "
                f"{position['shares']:.9f} shares | "
                f"Value: "
                f"${position['market_value']:.2f}"
            )

    print()

    open_orders = get_open_orders()

    print(
        f"Open orders: {len(open_orders)}"
    )

    print()
    print("No order was submitted.")