# ============================================================
# TRADING CONFIGURATION
# ============================================================

# Available modes:
#
# PAPER = Alpaca paper trading
# LIVE  = real-money trading
#
# IMPORTANT:
# LIVE trading is disabled by default.


TRADING_MODE = "PAPER"


# ============================================================
# PAPER TRADING
# ============================================================

PAPER_CONFIG = {
    # Your Alpaca paper account starts with $1,000
    "starting_capital": 1000.00,

    # Maximum amount allowed in one stock
    "max_position_value": 250.00,

    # Allow fractional shares
    "fractional_shares": True,

    # Safety restrictions
    "allow_leverage": False,
    "allow_short_selling": False,

    # Keep live trading disabled
    "live_trading_enabled": False
}


# ============================================================
# LIVE TRADING
# ============================================================

LIVE_CONFIG = {
    # The eventual live system will be designed
    # around a maximum of $30 of capital.
    "capital_limit": 30.00,

    # Allow fractional shares so small amounts
    # can be invested.
    "fractional_shares": True,

    # Safety restrictions
    "allow_leverage": False,
    "allow_short_selling": False,

    # IMPORTANT:
    # This must stay False while we are developing.
    "live_trading_enabled": False
}


# ============================================================
# GET ACTIVE CONFIGURATION
# ============================================================

def get_trading_config():

    mode = TRADING_MODE.upper()

    if mode == "PAPER":
        return PAPER_CONFIG

    if mode == "LIVE":
        return LIVE_CONFIG

    raise ValueError(
        f"Unknown trading mode: {mode}. "
        f"Use PAPER or LIVE."
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    config = get_trading_config()

    print("=" * 60)
    print("TRADING CONFIGURATION")
    print("=" * 60)

    print()
    print(f"Mode: {TRADING_MODE}")

    print()

    if TRADING_MODE == "PAPER":

        print(
            f"Paper capital: "
            f"${config['starting_capital']:.2f}"
        )

        print(
            f"Maximum position: "
            f"${config['max_position_value']:.2f}"
        )

    else:

        print(
            f"Live capital limit: "
            f"${config['capital_limit']:.2f}"
        )

    print(
        f"Fractional shares: "
        f"{config['fractional_shares']}"
    )

    print(
        f"Leverage: "
        f"{config['allow_leverage']}"
    )

    print(
        f"Short selling: "
        f"{config['allow_short_selling']}"
    )

    print(
        f"Live trading enabled: "
        f"{config['live_trading_enabled']}"
    )

    print()
    print("No orders were submitted.")