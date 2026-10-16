import os
import json
from datetime import datetime, timedelta, timezone

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

from market_config import get_symbols


# ============================================================
# SETTINGS
# ============================================================

MARKET = "US"

LOOKBACK_DAYS = 365

# Number of stocks passed to the AI
MAX_CANDIDATES = 15

# Minimum average daily dollar volume
MIN_AVG_DOLLAR_VOLUME = 10_000_000

OUTPUT_FILE = "screened_candidates.json"


# ============================================================
# ALPACA CONNECTION
# ============================================================

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    raise RuntimeError(
        "Alpaca API keys are missing."
    )

client = StockHistoricalDataClient(
    API_KEY,
    SECRET_KEY
)


# ============================================================
# GET HISTORICAL DATA
# ============================================================

def get_stock_history(symbol):

    end = datetime.now(timezone.utc)

    start = end - timedelta(
        days=LOOKBACK_DAYS
    )

    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        feed=DataFeed.IEX
    )

    try:

        bars = client.get_stock_bars(
            request
        )

        return list(bars[symbol])

    except Exception as error:

        print(
            f"WARNING: Could not retrieve "
            f"{symbol}: {error}"
        )

        return []


# ============================================================
# CALCULATE METRICS
# ============================================================

def calculate_metrics(symbol, bars):

    if len(bars) < 30:
        return None

    latest = bars[-1]

    current_price = float(
        latest.close
    )

    # --------------------------------------------------------
    # 30-DAY PERFORMANCE
    # --------------------------------------------------------

    price_30_days_ago = float(
        bars[-30].close
    )

    performance_30d = (
        (
            current_price
            / price_30_days_ago
        ) - 1
    ) * 100

    # --------------------------------------------------------
    # 1-YEAR PERFORMANCE
    # --------------------------------------------------------

    first_price = float(
        bars[0].close
    )

    performance_1y = (
        (
            current_price
            / first_price
        ) - 1
    ) * 100

    # --------------------------------------------------------
    # AVERAGE DOLLAR VOLUME
    # --------------------------------------------------------

    recent_bars = bars[-30:]

    dollar_volumes = []

    for bar in recent_bars:

        volume = float(
            bar.volume
        )

        close = float(
            bar.close
        )

        dollar_volumes.append(
            volume * close
        )

    average_dollar_volume = (
        sum(dollar_volumes)
        / len(dollar_volumes)
    )

    # --------------------------------------------------------
    # DISTANCE FROM 1-YEAR HIGH
    # --------------------------------------------------------

    one_year_high = max(
        float(bar.high)
        for bar in bars
    )

    distance_from_high = (
        (
            current_price
            / one_year_high
        ) - 1
    ) * 100

    # --------------------------------------------------------
    # SIMPLE SCREENING SCORE
    # --------------------------------------------------------

    score = 0

    # Liquidity
    if average_dollar_volume >= MIN_AVG_DOLLAR_VOLUME:
        score += 2

    # Positive yearly performance
    if performance_1y > 0:
        score += 2

    # Stronger yearly performance
    if performance_1y > 10:
        score += 1

    if performance_1y > 25:
        score += 1

    # Recent momentum
    if performance_30d > 0:
        score += 1

    if performance_30d > 5:
        score += 1

    return {
        "symbol": symbol,
        "price": current_price,
        "performance_30d": performance_30d,
        "performance_1y": performance_1y,
        "one_year_high": one_year_high,
        "distance_from_high_percent":
            distance_from_high,
        "average_dollar_volume":
            average_dollar_volume,
        "score": score
    }


# ============================================================
# SCREEN ALL STOCKS
# ============================================================

def screen_stocks():

    symbols = get_symbols(MARKET)

    results = []

    print()
    print(
        f"Screening {len(symbols)} US stocks..."
    )

    print()

    for index, symbol in enumerate(
        symbols,
        start=1
    ):

        print(
            f"[{index}/{len(symbols)}] "
            f"Checking {symbol}..."
        )

        bars = get_stock_history(
            symbol
        )

        metrics = calculate_metrics(
            symbol,
            bars
        )

        if metrics is not None:

            # Reject stocks with very low liquidity
            if (
                metrics["average_dollar_volume"]
                >= MIN_AVG_DOLLAR_VOLUME
            ):
                results.append(
                    metrics
                )

    # Highest score first
    results.sort(
        key=lambda x: (
            x["score"],
            x["performance_1y"],
            x["average_dollar_volume"]
        ),
        reverse=True
    )

    return results


# ============================================================
# SAVE CANDIDATES
# ============================================================

def save_candidates(candidates):

    output = {
        "generated_at":
            datetime.now(timezone.utc).isoformat(),

        "market": MARKET,

        "candidate_count":
            len(candidates),

        "candidates":
            candidates
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=4
        )

    print()
    print(
        f"Saved candidates to "
        f"{OUTPUT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("US STOCK SCREENER")
    print("=" * 70)

    results = screen_stocks()

    candidates = results[
        :MAX_CANDIDATES
    ]

    print()
    print("=" * 70)
    print(
        f"TOP {len(candidates)} AI CANDIDATES"
    )
    print("=" * 70)

    print()

    if not candidates:

        print(
            "No suitable stocks were found."
        )

    else:

        for rank, stock in enumerate(
            candidates,
            start=1
        ):

            print(
                f"{rank:2}. "
                f"{stock['symbol']:6} | "
                f"Price: "
                f"${stock['price']:.2f} | "
                f"30D: "
                f"{stock['performance_30d']:+.2f}% | "
                f"1Y: "
                f"{stock['performance_1y']:+.2f}% | "
                f"From High: "
                f"{stock['distance_from_high_percent']:+.2f}% | "
                f"Avg $ Volume: "
                f"${stock['average_dollar_volume']:,.0f} | "
                f"Score: "
                f"{stock['score']}"
            )

    save_candidates(candidates)

    print()
    print("=" * 70)
    print("SCREENING COMPLETE")
    print("=" * 70)

    print()
    print(
        "No orders were submitted."
    )