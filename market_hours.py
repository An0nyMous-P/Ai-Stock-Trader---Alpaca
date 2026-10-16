from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# US MARKET HOURS
# ============================================================

MARKET_HOURS = {
    "US": {
        "name": "United States",
        "timezone": "America/New_York",
        "open": (9, 30),
        "close": (16, 0),
    }
}


def get_market_status(market):
    """
    Return the current regular-session status.

    Supported market:
        US
    """

    market = market.upper()

    if market not in MARKET_HOURS:
        raise ValueError(
            f"Unknown market: {market}. "
            f"Supported markets: {', '.join(MARKET_HOURS)}"
        )

    config = MARKET_HOURS[market]

    now = datetime.now(
        ZoneInfo(config["timezone"])
    )

    # --------------------------------------------------------
    # WEEKEND
    # --------------------------------------------------------

    if now.weekday() >= 5:

        return {
            "market": market,
            "name": config["name"],
            "status": "CLOSED",
            "reason": "Weekend",
            "local_time": now.strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            ),
        }

    # --------------------------------------------------------
    # REGULAR SESSION
    # --------------------------------------------------------

    open_hour, open_minute = config["open"]
    close_hour, close_minute = config["close"]

    market_open = now.replace(
        hour=open_hour,
        minute=open_minute,
        second=0,
        microsecond=0,
    )

    market_close = now.replace(
        hour=close_hour,
        minute=close_minute,
        second=0,
        microsecond=0,
    )

    if market_open <= now < market_close:

        status = "OPEN"
        reason = "Regular trading hours"

    else:

        status = "CLOSED"
        reason = "Outside regular trading hours"

    return {
        "market": market,
        "name": config["name"],
        "status": status,
        "reason": reason,
        "local_time": now.strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        ),
    }


def print_market_status(market):
    """
    Print a readable market status.
    """

    status = get_market_status(market)

    print()
    print("=" * 60)
    print(f"{status['name'].upper()} MARKET")
    print("=" * 60)

    print(
        f"Status:      {status['status']}"
    )

    print(
        f"Reason:      {status['reason']}"
    )

    print(
        f"Local time:  {status['local_time']}"
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("US MARKET HOURS TEST")
    print("=" * 60)

    print_market_status("US")