# ============================================================
# RISK MANAGEMENT
# ============================================================

STARTING_PORTFOLIO = 1000.00

# No leverage.
ALLOW_LEVERAGE = False

# No short selling.
ALLOW_SHORT_SELLING = False

# ============================================================
# CHECK BUY
# ============================================================

def check_buy(
    portfolio_value,
    cash,
    current_position_value,
    proposed_buy_value
):
    """
    Check whether a proposed BUY is allowed.
    """

    reasons = []

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if proposed_buy_value <= 0:
        reasons.append(
            "Buy amount must be greater than $0."
        )

    if portfolio_value <= 0:
        reasons.append(
            "Portfolio value must be greater than $0."
        )

    # --------------------------------------------------------
    # Cash check
    # --------------------------------------------------------

    if proposed_buy_value > cash:
        reasons.append(
            "Not enough cash for this purchase."
        )

    # --------------------------------------------------------
    # Position size check
    # --------------------------------------------------------

    # No fixed position-size cap in paper trading.
    # The cash check above prevents spending more than
    # the available cash balance.

    # --------------------------------------------------------
    # Leverage check
    # --------------------------------------------------------

    if not ALLOW_LEVERAGE:
        if proposed_buy_value > cash:
            reasons.append(
                "Leverage is disabled."
            )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    if reasons:

        return {
            "allowed": False,
            "reason": " ".join(reasons)
        }

    return {
        "allowed": True,
        "reason": "BUY passes all risk checks."
    }


# ============================================================
# CHECK SELL
# ============================================================

def check_sell(
    current_position_value,
    proposed_sell_value
):
    """
    Check whether a proposed SELL is allowed.
    """

    reasons = []

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if proposed_sell_value <= 0:
        reasons.append(
            "Sell amount must be greater than $0."
        )

    # --------------------------------------------------------
    # Position check
    # --------------------------------------------------------

    if proposed_sell_value > current_position_value:
        reasons.append(
            "Cannot sell more value than the "
            "current position."
        )

    # --------------------------------------------------------
    # Short-selling protection
    # --------------------------------------------------------

    if not ALLOW_SHORT_SELLING:

        if proposed_sell_value > current_position_value:
            reasons.append(
                "Short selling is disabled."
            )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    if reasons:

        return {
            "allowed": False,
            "reason": " ".join(reasons)
        }

    return {
        "allowed": True,
        "reason": "SELL passes all risk checks."
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    portfolio = 1000.00
    cash = 1000.00
    current_position = 0.00

    print("=" * 60)
    print("RISK MANAGEMENT TEST")
    print("=" * 60)

    print()
    print(
        f"Starting portfolio: ${portfolio:,.2f}"
    )

    print(
        "Position limit: "
        "No fixed paper position limit"
    )

    print()

    # --------------------------------------------------------
    # Test 1: $250 BUY
    # --------------------------------------------------------

    result = check_buy(
        portfolio_value=portfolio,
        cash=cash,
        current_position_value=current_position,
        proposed_buy_value=250.00
    )

    print("Test 1: BUY $250")
    print("Allowed:", result["allowed"])
    print("Reason:", result["reason"])

    print()

    # --------------------------------------------------------
    # Test 2: $500 BUY
    # --------------------------------------------------------

    result = check_buy(
        portfolio_value=portfolio,
        cash=cash,
        current_position_value=current_position,
        proposed_buy_value=500.00
    )

    print("Test 2: BUY $500")
    print("Allowed:", result["allowed"])
    print("Reason:", result["reason"])

    print()

    # --------------------------------------------------------
    # Test 3: BUY $250 when already holding $100
    # --------------------------------------------------------

    result = check_buy(
        portfolio_value=portfolio,
        cash=900.00,
        current_position_value=100.00,
        proposed_buy_value=250.00
    )

    print("Test 3: BUY $250 with $100 already invested")
    print("Allowed:", result["allowed"])
    print("Reason:", result["reason"])

    print()

    # --------------------------------------------------------
    # Test 4: SELL with no position
    # --------------------------------------------------------

    result = check_sell(
        current_position_value=0.00,
        proposed_sell_value=100.00
    )

    print("Test 4: SELL $100 with no position")
    print("Allowed:", result["allowed"])
    print("Reason:", result["reason"])

    print()
    print("=" * 60)
    print("RISK MANAGEMENT TEST COMPLETE")
    print("=" * 60)
