import subprocess
import sys
import json
import os
import time
from datetime import datetime, timezone

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

from trading_config import get_trading_config


MARKET = "US"
CANDIDATE_FILE = "screened_candidates.json"

CHECK_INTERVAL_MINUTES = 5
AI_INTERVAL_MINUTES = 120

ORDER_LOG_FILE = "trade_log.jsonl"
ORDER_STATUS_CACHE_FILE = "order_status_cache.json"


# ============================================================
# ALPACA
# ============================================================

def get_trading_client():
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        raise RuntimeError("Alpaca API keys are missing.")

    # HARD SAFETY LOCK:
    # This bot is PAPER ONLY.
    return TradingClient(
        api_key,
        secret_key,
        paper=True
    )


# ============================================================
# MARKET
# ============================================================

def get_market_clock():
    client = get_trading_client()
    return client.get_clock()


def print_market_status():
    clock = get_market_clock()

    print()
    print("=" * 60)
    print("US MARKET")
    print("=" * 60)

    if clock.is_open:
        print("Status: OPEN")
        print("Next close:", clock.next_close)
    else:
        print("Status: CLOSED")
        print("Next open:", clock.next_open)

    return clock


# ============================================================
# ACCOUNT
# ============================================================

def get_account_state():
    client = get_trading_client()
    account = client.get_account()

    return {
        "cash": float(account.cash),
        "portfolio_value": float(account.portfolio_value),
        "buying_power": float(account.buying_power)
    }


def get_positions():
    client = get_trading_client()
    return client.get_all_positions()


def get_position(symbol):
    symbol = symbol.upper()

    positions = get_positions()

    for position in positions:
        if position.symbol.upper() == symbol:
            return position

    return None


def has_position_for_symbol(symbol):
    """
    Returns True if the paper account currently owns
    a positive quantity of the requested stock.
    """

    position = get_position(symbol)

    if position is None:
        return False

    try:
        quantity = float(position.qty)
    except (TypeError, ValueError):
        return False

    return quantity > 0


# ============================================================
# ORDERS
# ============================================================

def get_open_orders():
    client = get_trading_client()

    request = GetOrdersRequest(
        status=QueryOrderStatus.OPEN,
        limit=100
    )

    return client.get_orders(filter=request)


def get_recent_orders():
    client = get_trading_client()

    request = GetOrdersRequest(
        status=QueryOrderStatus.ALL,
        limit=50
    )

    return client.get_orders(filter=request)


def has_open_order_for_symbol(symbol):
    symbol = symbol.upper()

    orders = get_open_orders()

    for order in orders:
        if order.symbol.upper() == symbol:
            return True

    return False


def normalize_status(order):
    status = str(order.status)

    if "." in status:
        status = status.split(".")[-1]

    return status.upper()


# ============================================================
# ORDER LOGGING
# ============================================================

def load_order_status_cache():

    if not os.path.exists(ORDER_STATUS_CACHE_FILE):
        return {}

    try:
        with open(
            ORDER_STATUS_CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception:
        return {}


def save_order_status_cache(cache):

    with open(
        ORDER_STATUS_CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            cache,
            file,
            indent=2
        )


def log_order_event(order):

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "order_id": str(order.id),
        "symbol": order.symbol,
        "side": str(order.side),
        "status": normalize_status(order),
        "notional": (
            float(order.notional)
            if order.notional is not None
            else None
        ),
        "quantity": (
            float(order.qty)
            if order.qty is not None
            else None
        ),
        "filled_quantity": (
            float(order.filled_qty)
            if order.filled_qty is not None
            else None
        ),
        "filled_average_price": (
            float(order.filled_avg_price)
            if order.filled_avg_price is not None
            else None
        )
    }

    with open(
        ORDER_LOG_FILE,
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            json.dumps(event) + "\n"
        )


def monitor_order_statuses():

    orders = get_recent_orders()

    cache = load_order_status_cache()

    changes = []

    for order in orders:

        order_id = str(order.id)

        status = normalize_status(order)

        previous_status = cache.get(order_id)

        if previous_status != status:

            cache[order_id] = status

            log_order_event(order)

            changes.append(order)

    save_order_status_cache(cache)

    if changes:

        print()
        print("=" * 60)
        print("ORDER STATUS CHANGES")
        print("=" * 60)

        for order in changes:

            print()
            print("Order ID:", order.id)
            print("Symbol:", order.symbol)
            print("Side:", order.side)
            print("Status:", normalize_status(order))

            if order.filled_qty is not None:
                print(
                    "Filled quantity:",
                    order.filled_qty
                )

            if order.filled_avg_price is not None:
                print(
                    "Average fill:",
                    order.filled_avg_price
                )

    return changes


def display_open_orders():

    orders = get_open_orders()

    print()
    print("=" * 60)
    print("OPEN ORDERS")
    print("=" * 60)

    if not orders:

        print("None")

        return orders

    for order in orders:

        print()

        print("Order ID:", order.id)
        print("Symbol:", order.symbol)
        print("Side:", order.side)
        print("Status:", normalize_status(order))

        if order.notional is not None:
            print("Notional:", order.notional)

        if order.qty is not None:
            print("Quantity:", order.qty)

        if order.filled_qty is not None:
            print(
                "Filled quantity:",
                order.filled_qty
            )

    return orders


# ============================================================
# ACCOUNT DISPLAY
# ============================================================

def print_account():

    state = get_account_state()

    print()
    print("=" * 60)
    print("PAPER ACCOUNT")
    print("=" * 60)

    print()
    print(
        f"Cash: ${state['cash']:,.2f}"
    )

    print(
        f"Portfolio: ${state['portfolio_value']:,.2f}"
    )

    print(
        f"Buying power: ${state['buying_power']:,.2f}"
    )

    positions = get_positions()

    print()

    if not positions:

        print("Positions: None")

    else:

        print("Positions:")

        for position in positions:

            print(
                f"  {position.symbol}: "
                f"{position.qty} shares | "
                f"Market value "
                f"${float(position.market_value):,.2f} | "
                f"P/L "
                f"${float(position.unrealized_pl):,.2f}"
            )


# ============================================================
# RUN OTHER SCRIPTS
# ============================================================

def run_script(script_name):

    print()
    print("=" * 60)
    print(f"RUNNING {script_name}")
    print("=" * 60)

    result = subprocess.run(
        [
            sys.executable,
            script_name
        ],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:

        print(result.stderr)

        raise RuntimeError(
            f"{script_name} failed "
            f"with exit code {result.returncode}"
        )

    return result.stdout


# ============================================================
# CANDIDATES
# ============================================================

def load_candidates():

    if not os.path.exists(
        CANDIDATE_FILE
    ):

        raise FileNotFoundError(
            f"{CANDIDATE_FILE} was not found."
        )

    with open(
        CANDIDATE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# AI DECISION PARSER
# ============================================================

def extract_ai_decision(output):

    action = None
    allocation = 0.0

    for line in output.splitlines():

        line = line.strip()

        if line.startswith("Final action:"):

            action = (
                line
                .split(":", 1)[1]
                .strip()
            )

        elif line.startswith("Final allocation:"):

            value = (
                line
                .split(":", 1)[1]
                .strip()
                .replace("$", "")
            )

            allocation = float(value)

        elif line.startswith("FINAL ACTION:"):

            action = (
                line
                .split(":", 1)[1]
                .strip()
            )

        elif line.startswith("ALLOCATION:"):

            value = (
                line
                .split(":", 1)[1]
                .strip()
                .replace("$", "")
            )

            allocation = float(value)

    if not action:

        raise RuntimeError(
            "Could not find the AI final action."
        )

    return action.upper(), allocation


# ============================================================
# PAPER BUY
# ============================================================

def submit_buy(symbol, allocation):

    client = get_trading_client()

    order = MarketOrderRequest(
        symbol=symbol,
        notional=round(
            allocation,
            2
        ),
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )

    return client.submit_order(
        order_data=order
    )


# ============================================================
# PAPER SELL
# ============================================================

def submit_sell(symbol):

    client = get_trading_client()

    position = get_position(symbol)

    if position is None:

        raise RuntimeError(
            f"No {symbol} position exists to sell."
        )

    quantity = float(position.qty)

    if quantity <= 0:

        raise RuntimeError(
            f"Invalid {symbol} position quantity: "
            f"{quantity}"
        )

    order = MarketOrderRequest(
        symbol=symbol,
        qty=quantity,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY
    )

    return client.submit_order(
        order_data=order
    )


# ============================================================
# AI TRADING CYCLE
# ============================================================

def run_ai_cycle():

    print()
    print("=" * 60)
    print("STARTING AI TRADING DECISION")
    print("=" * 60)

    print_account()

    # Run screener
    run_script(
        "stock_screener.py"
    )

    candidates = load_candidates()

    print()
    print(
        "Screened candidates:",
        candidates["candidate_count"]
    )

    # Run AI
    ai_output = run_script(
        "ai_analysis.py"
    )

    action, allocation = extract_ai_decision(
        ai_output
    )

    print()
    print("=" * 60)
    print("AI DECISION")
    print("=" * 60)

    print()
    print("Action:", action)

    if action.startswith("BUY"):

        print(
            f"Allocation: "
            f"${allocation:.2f}"
        )

    # ========================================================
    # HOLD
    # ========================================================

    if action == "HOLD":

        print()
        print("AI chose HOLD.")
        print("No order submitted.")

        return

    # ========================================================
    # PARSE COMMAND
    # ========================================================

    parts = action.split()

    if len(parts) != 2:

        raise RuntimeError(
            f"Invalid AI action format: "
            f"{action}"
        )

    command = parts[0].upper()
    symbol = parts[1].upper()

    if command not in {
        "BUY",
        "SELL"
    }:

        raise RuntimeError(
            f"Unsupported AI command: "
            f"{command}"
        )

    # ========================================================
    # SELL
    # ========================================================

    if command == "SELL":

        print()
        print("=" * 60)
        print("AI SELL DECISION")
        print("=" * 60)

        position = get_position(symbol)

        if position is None:

            print()
            print(
                f"No {symbol} position exists."
            )

            print(
                "SELL skipped."
            )

            print(
                "Short selling is disabled."
            )

            return

        if has_open_order_for_symbol(symbol):

            print()
            print(
                f"An open order already exists "
                f"for {symbol}."
            )

            print(
                "SELL skipped."
            )

            return

        quantity = float(position.qty)

        market_value = float(
            position.market_value
        )

        print()
        print(
            f"Position: {symbol}"
        )

        print(
            f"Shares: {quantity}"
        )

        print(
            f"Market value: "
            f"${market_value:,.2f}"
        )

        print()
        print("Safety checks:")
        print("  ✓ PAPER mode")
        print("  ✓ Live trading disabled")
        print("  ✓ Existing position confirmed")
        print("  ✓ No existing order")
        print("  ✓ Short selling disabled")

        print()
        print(
            "Submitting PAPER SELL automatically..."
        )

        order = submit_sell(symbol)

        print()
        print("=" * 60)
        print("PAPER SELL ORDER SUBMITTED")
        print("=" * 60)

        print()
        print("Order ID:", order.id)
        print("Symbol:", order.symbol)
        print("Side:", order.side)
        print("Quantity:", order.qty)
        print("Status:", order.status)

        log_order_event(order)

        return

    # ========================================================
    # BUY
    # ========================================================

    if command == "BUY":

        screened_symbols = {
            candidate["symbol"].upper()
            for candidate
            in candidates["candidates"]
        }

        if symbol not in screened_symbols:

            raise RuntimeError(
                f"{symbol} is not in the "
                f"screened candidate list."
            )

        if allocation > account["cash"]:

            raise RuntimeError(
                f"AI proposed "
                f"${allocation:.2f}, "
                f"but only "
                f"${account['cash']:.2f} "
                f"paper cash is available."
            )

        # ----------------------------------------------------
        # POSITION CHECK
        # ----------------------------------------------------

        if has_position_for_symbol(symbol):

            position = get_position(symbol)

            print()
            print(
                f"A {symbol} position "
                f"already exists."
            )

            print(
                f"Current market value: "
                f"${float(position.market_value):,.2f}"
            )

            print()
            print(
                "BUY skipped to prevent "
                "automatic position stacking."
            )

            return

        # ----------------------------------------------------
        # OPEN ORDER CHECK
        # ----------------------------------------------------

        if has_open_order_for_symbol(symbol):

            print()
            print(
                f"An open order already exists "
                f"for {symbol}."
            )

            print(
                "BUY skipped."
            )

            return

        # ----------------------------------------------------
        # CASH CHECK
        # ----------------------------------------------------

        account = get_account_state()

        if allocation > account["cash"]:

            print()
            print(
                f"Insufficient cash for "
                f"${allocation:.2f} BUY."
            )

            print(
                f"Available cash: "
                f"${account['cash']:.2f}"
            )

            return

        # ----------------------------------------------------
        # FINAL PAPER SAFETY CHECK
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("AUTOMATIC PAPER BUY")
        print("=" * 60)

        print()
        print(
            f"BUY {symbol}"
        )

        print(
            f"Allocation: "
            f"${allocation:.2f}"
        )

        print()
        print("Safety checks:")
        print("  ✓ PAPER mode")
        print("  ✓ Live trading disabled")
        print("  ✓ Market open")
        print("  ✓ Candidate screened")
        print("  ✓ No existing position")
        print("  ✓ No existing order")
        print("  ✓ Allocation within available paper cash")
        print("  ✓ Sufficient cash")

        print()
        print(
            "Submitting PAPER BUY automatically..."
        )

        order = submit_buy(
            symbol,
            allocation
        )

        print()
        print("=" * 60)
        print("PAPER BUY ORDER SUBMITTED")
        print("=" * 60)

        print()
        print("Order ID:", order.id)
        print("Symbol:", order.symbol)
        print("Side:", order.side)
        print("Notional:", order.notional)
        print("Status:", order.status)

        log_order_event(order)


# ============================================================
# MAIN LOOP
# ============================================================

def main():

    print()
    print("=" * 60)
    print("AUTONOMOUS AI PAPER TRADING BOT")
    print("=" * 60)

    config = get_trading_config()

    # HARD SAFETY LOCK
    if config.get(
        "live_trading_enabled",
        False
    ):

        raise RuntimeError(
            "LIVE TRADING IS NOT ALLOWED."
        )

    print()
    print("Trading mode: PAPER")
    print("Live trading: DISABLED")
    print("Market: US")

    print(
        f"Order check interval: "
        f"{CHECK_INTERVAL_MINUTES} minutes"
    )

    print(
        f"AI decision interval: "
        f"{AI_INTERVAL_MINUTES} minutes"
    )

    print(
        "AI BUY allocation: "
        "up to available paper cash"
    )

    print(
        "The bot will run continuously."
    )

    print(
        "No manual order checking is required."
    )

    print(
        "Press CTRL+C to stop it."
    )

    last_ai_run = None

    while True:

        try:

            print()
            print("=" * 60)
            print("BOT CHECK")
            print("=" * 60)

            print()
            print(
                "Check time:",
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            # Monitor existing orders
            monitor_order_statuses()

            # Check open orders
            open_orders = display_open_orders()

            if open_orders:

                print()
                print(
                    "An order is currently "
                    "open or processing."
                )

                print(
                    "AI trading is paused "
                    "to prevent duplicate orders."
                )

            else:

                # Check market
                clock = print_market_status()

                if not clock.is_open:

                    print()
                    print(
                        "Market is closed."
                    )

                    print(
                        "No AI trading decision "
                        "will be made."
                    )

                else:

                    now = datetime.now(
                        timezone.utc
                    )

                    should_run_ai = (
                        last_ai_run is None
                        or
                        (
                            now - last_ai_run
                        ).total_seconds()
                        >=
                        AI_INTERVAL_MINUTES * 60
                    )

                    if should_run_ai:

                        run_ai_cycle()

                        last_ai_run = now

                    else:

                        elapsed = (
                            now - last_ai_run
                        ).total_seconds()

                        remaining = max(
                            0,
                            AI_INTERVAL_MINUTES * 60
                            - elapsed
                        )

                        print()
                        print(
                            "AI cooldown active."
                        )

                        print(
                            f"Next AI decision "
                            f"in {remaining / 60:.1f} minutes."
                        )

        except KeyboardInterrupt:

            print()
            print("=" * 60)
            print("BOT STOPPED")
            print("=" * 60)

            return

        except Exception as error:

            print()
            print("=" * 60)
            print("BOT ERROR")
            print("=" * 60)

            print()

            print(
                type(error).__name__
                + ":",
                error
            )

            print()
            print(
                "The bot will continue "
                "after the next check."
            )

        print()
        print("=" * 60)
        print(
            f"WAITING "
            f"{CHECK_INTERVAL_MINUTES} MINUTES"
        )
        print("=" * 60)

        try:

            time.sleep(
                CHECK_INTERVAL_MINUTES * 60
            )

        except KeyboardInterrupt:

            print()
            print("=" * 60)
            print("BOT STOPPED")
            print("=" * 60)

            return


if __name__ == "__main__":
    main()
