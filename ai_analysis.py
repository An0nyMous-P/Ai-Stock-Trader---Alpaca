import os
import re
import json
from datetime import datetime, timedelta, timezone

import requests
from openai import OpenAI

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import (
    StockLatestTradeRequest,
    StockBarsRequest,
)
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

from alpaca.trading.client import TradingClient

from risk_manager import check_buy, check_sell
from sec_company_lookup import build_ticker_lookup


# ============================================================
# SETTINGS
# ============================================================

CANDIDATE_FILE = "screened_candidates.json"

HISTORY_DAYS = 365

SEC_USER_AGENT = "AI Trading research@example.com"


# ============================================================
# API KEYS
# ============================================================

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    raise RuntimeError(
        "Alpaca API keys are missing."
    )


# ============================================================
# CLIENTS
# ============================================================

data_client = StockHistoricalDataClient(
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY
)

trading_client = TradingClient(
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
    paper=True
)

openai_client = OpenAI()


# ============================================================
# SAFE FORMATTERS
# ============================================================

def format_number(value, decimals=2):

    if value is None:
        return "unavailable"

    try:
        return f"{float(value):.{decimals}f}"

    except (TypeError, ValueError):
        return "unavailable"


def format_money(value):

    if value is None:
        return "unavailable"

    try:
        return f"${float(value):,.2f}"

    except (TypeError, ValueError):
        return "unavailable"


# ============================================================
# LOAD SCREENED CANDIDATES
# ============================================================

def load_candidates():

    if not os.path.exists(CANDIDATE_FILE):

        raise RuntimeError(
            f"{CANDIDATE_FILE} was not found. "
            f"Run stock_screener.py first."
        )

    with open(
        CANDIDATE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    candidates = data.get(
        "candidates",
        []
    )

    if not candidates:

        raise RuntimeError(
            "No screened candidates were found."
        )

    return candidates


# ============================================================
# ACCOUNT
# ============================================================

def get_account_state():

    account = trading_client.get_account()

    return {
        "cash": float(account.cash),
        "portfolio_value": float(
            account.portfolio_value
        ),
        "buying_power": float(
            account.buying_power
        )
    }


# ============================================================
# POSITIONS
# ============================================================

def get_positions(symbols):

    positions = {}

    for symbol in symbols:

        try:

            position = trading_client.get_open_position(
                symbol
            )

            positions[symbol] = {
                "shares": float(
                    position.qty
                ),

                "market_value": float(
                    position.market_value
                ),

                "unrealized_pl": float(
                    position.unrealized_pl
                ),

                "average_entry_price": float(
                    position.avg_entry_price
                )
            }

        except Exception:

            positions[symbol] = {
                "shares": 0.0,
                "market_value": 0.0,
                "unrealized_pl": 0.0,
                "average_entry_price": 0.0
            }

    return positions


# ============================================================
# CURRENT PRICES
# ============================================================

def get_current_prices(symbols):

    request = StockLatestTradeRequest(
        symbol_or_symbols=symbols
    )

    trades = data_client.get_stock_latest_trade(
        request
    )

    prices = {}

    for symbol in symbols:

        try:

            prices[symbol] = float(
                trades[symbol].price
            )

        except Exception:

            prices[symbol] = None

    return prices


# ============================================================
# HISTORICAL DATA
# ============================================================

def get_historical_data(symbols):

    end = datetime.now(timezone.utc)

    start = end - timedelta(
        days=HISTORY_DAYS
    )

    request = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        feed=DataFeed.IEX
    )

    bars = data_client.get_stock_bars(
        request
    )

    historical = {}

    for symbol in symbols:

        try:

            historical[symbol] = list(
                bars[symbol]
            )

        except Exception:

            historical[symbol] = []

    return historical


# ============================================================
# HISTORY SUMMARY
# ============================================================

def summarize_history(
    bars,
    current_price
):

    if not bars:

        return {
            "current_price": current_price,
            "starting_close": None,
            "one_year_change_percent": None,
            "recent_close": None,
            "recent_change_percent": None,
            "one_year_high": None,
            "distance_from_high_percent": None
        }

    starting_close = float(
        bars[0].close
    )

    recent_close = float(
        bars[-1].close
    )

    one_year_high = max(
        float(bar.high)
        for bar in bars
    )

    if (
        current_price is not None
        and starting_close != 0
    ):

        one_year_change = (
            (
                current_price
                - starting_close
            )
            / starting_close
        ) * 100

    else:

        one_year_change = None

    if len(bars) >= 6:

        previous_close = float(
            bars[-6].close
        )

        if (
            current_price is not None
            and previous_close != 0
        ):

            recent_change = (
                (
                    current_price
                    - previous_close
                )
                / previous_close
            ) * 100

        else:

            recent_change = None

    else:

        recent_change = None

    if (
        current_price is not None
        and one_year_high != 0
    ):

        distance_from_high = (
            (
                current_price
                - one_year_high
            )
            / one_year_high
        ) * 100

    else:

        distance_from_high = None

    return {
        "current_price": current_price,
        "starting_close": starting_close,
        "one_year_change_percent":
            one_year_change,
        "recent_close": recent_close,
        "recent_change_percent":
            recent_change,
        "one_year_high": one_year_high,
        "distance_from_high_percent":
            distance_from_high
    }


# ============================================================
# SEC COMPANY FACTS
# ============================================================

def get_sec_company_facts(
    symbol,
    ticker_lookup
):

    cik = ticker_lookup.get(
        symbol.upper()
    )

    if cik is None:

        raise RuntimeError(
            f"SEC CIK not found for {symbol}"
        )

    url = (
        "https://data.sec.gov/api/xbrl/"
        "companyfacts/"
        f"CIK{cik}.json"
    )

    response = requests.get(
        url,
        headers={
            "User-Agent": SEC_USER_AGENT
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# SEC QUARTERLY VALUE
# ============================================================

def get_latest_value(
    facts,
    tag,
    days_limit=100
):

    try:

        units = facts[
            "facts"
        ][
            "us-gaap"
        ][
            tag
        ][
            "units"
        ]

    except KeyError:

        return None

    candidates = []

    cutoff = (
        datetime.now(timezone.utc).date()
        - timedelta(days=days_limit)
    )

    for entries in units.values():

        for entry in entries:

            value = entry.get("val")
            filed = entry.get("filed")

            if value is None or filed is None:
                continue

            try:

                filed_date = datetime.strptime(
                    filed,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                continue

            if filed_date < cutoff:
                continue

            form = entry.get(
                "form",
                ""
            )

            if form not in (
                "10-Q",
                "10-K"
            ):
                continue

            candidates.append(
                (
                    filed_date,
                    value
                )
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidates[0][1]


# ============================================================
# SEC POINT-IN-TIME VALUE
# ============================================================

def get_latest_point_value(
    facts,
    tag
):

    try:

        units = facts[
            "facts"
        ][
            "us-gaap"
        ][
            tag
        ][
            "units"
        ]

    except KeyError:

        return None

    candidates = []

    for entries in units.values():

        for entry in entries:

            value = entry.get("val")
            filed = entry.get("filed")

            if value is None or filed is None:
                continue

            try:

                filed_date = datetime.strptime(
                    filed,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                continue

            candidates.append(
                (
                    filed_date,
                    value
                )
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidates[0][1]


# ============================================================
# FINANCIAL DATA
# ============================================================

def get_financial_data(
    symbol,
    ticker_lookup
):

    facts = get_sec_company_facts(
        symbol,
        ticker_lookup
    )

    quarterly_tags = {

        "Revenue":
            "RevenueFromContractWithCustomerExcludingAssessedTax",

        "Net Income":
            "NetIncomeLoss",

        "Gross Profit":
            "GrossProfit",

        "Operating Income":
            "OperatingIncomeLoss",

        "Diluted EPS":
            "EarningsPerShareDiluted",

        "R&D Expense":
            "ResearchAndDevelopmentExpense"
    }

    balance_tags = {

        "Cash":
            "CashAndCashEquivalentsAtCarryingValue",

        "Long-Term Debt":
            "LongTermDebt",

        "Total Assets":
            "Assets",

        "Total Liabilities":
            "Liabilities"
    }

    financials = {}

    for name, tag in quarterly_tags.items():

        financials[name] = get_latest_value(
            facts,
            tag
        )

    for name, tag in balance_tags.items():

        financials[name] = get_latest_point_value(
            facts,
            tag
        )

    return financials


# ============================================================
# FORMAT FINANCIALS
# ============================================================

def format_financials(financials):

    lines = []

    for name, value in financials.items():

        if value is None:

            lines.append(
                f"- {name}: unavailable"
            )

            continue

        if name == "Diluted EPS":

            lines.append(
                f"- {name}: "
                f"${float(value):.2f}"
            )

        else:

            lines.append(
                f"- {name}: "
                f"${float(value):,.0f}"
            )

    return "\n".join(lines)


# ============================================================
# EXTRACT AI ACTION
# ============================================================

def extract_action(ai_output):

    match = re.search(
        r"FINAL ACTION:\s*"
        r"(BUY|SELL)\s+([A-Z.]+)"
        r"|FINAL ACTION:\s*(HOLD)",
        ai_output,
        re.IGNORECASE
    )

    if not match:

        raise RuntimeError(
            "AI did not return a valid FINAL ACTION."
        )

    if match.group(1):

        return (
            match.group(1).upper(),
            match.group(2).upper()
        )

    return (
        "HOLD",
        None
    )


# ============================================================
# EXTRACT ALLOCATION
# ============================================================

def extract_allocation(
    ai_output,
    action
):

    if action != "BUY":
        return 0.0

    match = re.search(
        r"ALLOCATION:\s*\$?\s*"
        r"([0-9]+(?:\.[0-9]+)?)",
        ai_output,
        re.IGNORECASE
    )

    if not match:

        raise RuntimeError(
            "AI BUY decision did not include "
            "an ALLOCATION."
        )

    return float(
        match.group(1)
    )


# ============================================================
# AI ANALYSIS
# ============================================================

def run_ai_analysis():

    print()
    print("=" * 60)
    print("LOADING SCREENED CANDIDATES")
    print("=" * 60)

    candidates = load_candidates()

    stocks = [
        item["symbol"]
        for item in candidates
    ]

    print()

    print(
        f"AI candidates: {len(stocks)}"
    )

    print(
        ", ".join(stocks)
    )

    print()
    print("=" * 60)
    print("COLLECTING FRESH TRADING DATA")
    print("=" * 60)

    account = get_account_state()

    positions = get_positions(
        stocks
    )

    prices = get_current_prices(
        stocks
    )

    historical = get_historical_data(
        stocks
    )

    ticker_lookup = build_ticker_lookup()

    financials = {}

    history_summaries = {}

    for symbol in stocks:

        try:

            financials[symbol] = (
                get_financial_data(
                    symbol,
                    ticker_lookup
                )
            )

        except Exception as error:

            print()
            print(
                f"SEC data failed for "
                f"{symbol}: {error}"
            )

            financials[symbol] = {}

        history_summaries[symbol] = (
            summarize_history(
                historical.get(
                    symbol,
                    []
                ),
                prices.get(symbol)
            )
        )

    # ========================================================
    # STOCK INFORMATION
    # ========================================================

    stock_information = []

    for candidate in candidates:

        symbol = candidate["symbol"]

        position = positions[symbol]

        history = history_summaries[symbol]

        financial = financials[symbol]

        stock_information.append(
            f"""
============================================================
{symbol}
============================================================

SCREENING SCORE:
{candidate['score']}

CURRENT PRICE:
{format_money(history['current_price'])}

30-DAY PERFORMANCE:
{format_number(candidate['performance_30d'])}%

ONE-YEAR PERFORMANCE:
{format_number(candidate['performance_1y'])}%

ONE-YEAR HIGH:
{format_money(candidate['one_year_high'])}

DISTANCE FROM ONE-YEAR HIGH:
{format_number(candidate['distance_from_high_percent'])}%

AVERAGE DOLLAR VOLUME:
{format_money(candidate['average_dollar_volume'])}

CURRENT PAPER POSITION:
Shares: {position['shares']}
Market value: {format_money(position['market_value'])}
Unrealized P/L: {format_money(position['unrealized_pl'])}
Average entry price: {format_money(position['average_entry_price'])}

SEC FINANCIAL DATA:
{format_financials(financial)}

Operating cash flow:
DO NOT USE OR REPORT.
"""
        )

    # ========================================================
    # PORTFOLIO
    # ========================================================

    portfolio_positions = []

    all_positions = trading_client.get_all_positions()

    for position in all_positions:

        portfolio_positions.append(
            f"{position.symbol}: "
            f"{float(position.qty):.9f} shares, "
            f"{format_money(float(position.market_value))} value"
        )

    if portfolio_positions:

        portfolio_text = "\n".join(
            portfolio_positions
        )

    else:

        portfolio_text = "No current positions."

    # ========================================================
    # AI PROMPT
    # ========================================================

    prompt = f"""
You are the decision-making investment analyst
for an autonomous PAPER trading system.

Today is {datetime.now().strftime('%Y-%m-%d')}.

The stock screener selected these candidates:

{', '.join(stocks)}

You must deeply analyze these candidates.

Current paper portfolio:

Cash: ${account['cash']:,.2f}
Portfolio value: ${account['portfolio_value']:,.2f}
Buying power: ${account['buying_power']:,.2f}

Current positions:

{portfolio_text}

The system is PAPER TRADING ONLY.

Use web search to research important recent news
before making the final decision.

Consider:

- Earnings
- Revenue growth
- Profitability
- Valuation
- Products
- AI developments
- Management
- Competition
- Regulation
- Partnerships
- Supply chain
- Legal issues
- Government actions
- Other material events

Do not invent facts.

============================================================
INVESTMENT PRINCIPLES
============================================================

Do NOT simply buy the stock that rose the most.

Do NOT simply sell a stock because its price fell.

Do NOT panic sell.

A falling stock must be evaluated based on whether
the underlying investment thesis has deteriorated.

Consider:

- Business quality
- Revenue growth
- Earnings growth
- Profit margins
- Competitive advantages
- Balance-sheet strength
- Management
- Product pipeline
- AI opportunities
- Industry position
- Risks
- Valuation
- Recent news
- Price trend
- Risk/reward
- Existing portfolio exposure

A strong company can remain HOLD after a decline
if the long-term thesis remains intact.

A stock near a high is NOT automatically a SELL.

A stock that has fallen is NOT automatically a BUY.

Valuation matters.

============================================================
PORTFOLIO RULES
============================================================

The current PAPER portfolio is approximately
${account['portfolio_value']:,.2f}.

There is no fixed maximum paper BUY allocation.

The AI may allocate any amount from $1.00 up to the
currently available paper cash, based on conviction,
valuation, financial quality, expected return, risk,
portfolio concentration, and the strength of the investment thesis.

Do not assume the system needs to spread money evenly
between stocks.

Fractional shares are supported.

If buying a stock, specify a dollar allocation.

The allocation must be at least $1.00 and must not exceed
the currently available paper cash.

For example:

ALLOCATION: $75.50

means invest exactly $75.50.

No leverage.

No short selling.

Only ONE stock may receive a BUY decision
per analysis cycle.

Do not assume the system needs to buy a whole share.

For example:

ALLOCATION: $7.50

means invest exactly $7.50.

No leverage.

No short selling.

Only ONE stock may receive a BUY decision
per analysis cycle.

============================================================
SELL RULE
============================================================

Do NOT recommend SELL merely because:

- the stock increased in price
- the position is profitable
- the stock reached a recent high
- the stock reached an all-time high
- the stock has already made a large gain
- the stock is slightly overbought
- the AI wants to take a quick profit
- the stock dropped today
- the stock dropped this week
- the stock is below its purchase price
- the stock is experiencing normal volatility

If the investment thesis remains strong, prefer HOLD.

If a stock rises substantially but its fundamentals,
future prospects, competitive position and valuation
still support holding it, HOLD rather than taking profit.

Do not panic-sell because of a normal temporary decline.

SELL only when there is a meaningful reason such as:

- the investment thesis has materially deteriorated
- important fundamentals have materially weakened
- management decisions seriously damage the thesis
- the long-term growth outlook has materially deteriorated
- valuation becomes so extreme that expected future
  returns are no longer attractive
- a serious company-specific risk changes the thesis
- a substantially better use of capital exists
- a predefined risk-control condition requires exiting

When an existing position is still fundamentally healthy,
HOLD is preferred over selling simply to realize a profit.

============================================================
FINANCIAL DATA RULE
============================================================

Use the supplied SEC financial data.

Operating cash flow is intentionally excluded.

Do NOT report or rely on operating cash flow.

============================================================
DECISION FORMAT
============================================================

After researching the candidates:

1. Rank all candidates from most attractive
   to least attractive.

2. Explain each ranking briefly.

3. Identify the best BUY candidate, if any.

4. Identify existing positions that should HOLD.

5. Identify existing positions that should SELL,
   if any.

6. Give one final portfolio action.

The final action MUST use this format:

FINAL ACTION: BUY <TICKER>

or

FINAL ACTION: SELL <TICKER>

or

FINAL ACTION: HOLD

If the final action is BUY, you MUST also output:

ALLOCATION: $<amount>

The allocation must be at least $1.00 and must not exceed
the currently available paper cash.

If the final action is SELL, no allocation is required.

At the very end output exactly:

FINAL ACTION: <action>

ALLOCATION: $<amount>

FINAL CONFIDENCE: <0-100>%

FINAL REASON:
<short explanation>

Here is the supplied market, screening,
historical and financial data:

{''.join(stock_information)}
"""

    # ========================================================
    # OPENAI
    # ========================================================

    print()
    print("=" * 60)
    print("RUNNING FRESH AI ANALYSIS")
    print("=" * 60)

    response = openai_client.responses.create(
        model="gpt-5.6-luna",
        tools=[
            {
                "type": "web_search"
            }
        ],
        input=prompt
    )

    ai_output = response.output_text

    # ========================================================
    # EXTRACT DECISION
    # ========================================================

    action, symbol = extract_action(
        ai_output
    )

    allocation = extract_allocation(
        ai_output,
        action
    )

    # ========================================================
    # SAFETY VALIDATION
    # ========================================================

    if action == "BUY":

        if symbol not in stocks:

            raise RuntimeError(
                f"AI attempted to BUY {symbol}, "
                f"but it was not one of the screened "
                f"candidates."
            )

        if allocation > account["cash"]:

            raise RuntimeError(
                "AI BUY allocation exceeds "
                f"available paper cash of ${account['cash']:.2f}."
            )

    # ========================================================
    # RISK MANAGEMENT
    # ========================================================

    if action == "HOLD":

        risk_result = {
            "allowed": True,
            "reason": "HOLD requires no trade."
        }

    else:

        current_position_value = (
            positions[symbol]["market_value"]
        )

        if action == "BUY":

            risk_result = check_buy(
                account["portfolio_value"],
                account["cash"],
                current_position_value,
                allocation
            )

        elif action == "SELL":

            risk_result = check_sell(
                current_position_value,
                current_position_value
            )

        else:

            risk_result = {
                "allowed": False,
                "reason": "Invalid action."
            }

    # ========================================================
    # DISPLAY
    # ========================================================

    print()
    print("=" * 60)
    print("AI TRADING ANALYSIS")
    print("=" * 60)

    print()
    print(ai_output)

    print()
    print("=" * 60)
    print("RISK MANAGEMENT")
    print("=" * 60)

    print(
        f"AI action: "
        f"{action} "
        f"{symbol if symbol else ''}"
    )

    if action == "BUY":

        print(
            f"AI allocation: "
            f"${allocation:.2f}"
        )

    print(
        f"Risk check allowed: "
        f"{risk_result['allowed']}"
    )

    print(
        f"Risk check reason: "
        f"{risk_result['reason']}"
    )

    print()
    print("=" * 60)
    print("AI ANALYSIS COMPLETE")
    print("=" * 60)

    print()

    print(
        f"Final action: "
        f"{action} "
        f"{symbol if symbol else ''}"
    )

    if action == "BUY":

        print(
            f"Final allocation: "
            f"${allocation:.2f}"
        )

    return {
        "stocks": stocks,
        "cash": account["cash"],
        "portfolio_value":
            account["portfolio_value"],
        "buying_power":
            account["buying_power"],
        "prices": prices,
        "positions": positions,
        "financials": financials,
        "history_summaries":
            history_summaries,
        "ai_output": ai_output,
        "ai_action": (
            f"{action} {symbol}"
            if symbol
            else "HOLD"
        ),
        "allocation": allocation,
        "risk_result": risk_result
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    result = run_ai_analysis()

    print()
    print("=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    print()

    print(
        f"AI action: "
        f"{result['ai_action']}"
    )

    if result["allocation"] > 0:

        print(
            f"AI allocation: "
            f"${result['allocation']:.2f}"
        )

    print(
        f"Risk allowed: "
        f"{result['risk_result']['allowed']}"
    )
