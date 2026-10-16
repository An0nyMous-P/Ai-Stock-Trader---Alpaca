# ============================================================
# US MARKET CONFIGURATION
# ============================================================

MARKETS = {
    "US": {
        "name": "United States",
        "currency": "USD",
        "exchanges": [
            "NYSE",
            "NASDAQ"
        ],
        "clock": "NYSE",

        # The AI is NOT restricted to only these companies.
        # This is the initial liquid large-cap universe.
        "symbols": [
            "AAPL",
            "MSFT",
            "NVDA",
            "GOOGL",
            "GOOG",
            "AMZN",
            "META",
            "AVGO",
            "TSLA",
            "BRK.B",
            "JPM",
            "V",
            "MA",
            "LLY",
            "JNJ",
            "WMT",
            "COST",
            "HD",
            "PG",
            "KO",
            "PEP",
            "ORCL",
            "CRM",
            "NFLX",
            "AMD",
            "ADBE",
            "CSCO",
            "QCOM",
            "INTC",
            "TXN",
            "AMAT",
            "MU",
            "INTU",
            "NOW",
            "UBER",
            "ABNB",
            "SHOP",
            "PLTR",
            "PANW",
            "CRWD",
            "SNOW",
            "GE",
            "CAT",
            "RTX",
            "HON",
            "BA",
            "XOM",
            "CVX",
            "COP",
            "UNH",
            "MRK",
            "ABBV",
            "TMO",
            "ISRG",
            "MCD",
            "NKE",
            "SBUX",
            "DIS",
            "CMCSA",
            "T",
            "VZ"
        ]
    }
}


# ============================================================
# MARKET CONFIG
# ============================================================

def get_market_config(market):

    market = market.upper()

    if market not in MARKETS:
        raise ValueError(
            f"Unknown market: {market}"
        )

    return MARKETS[market]


# ============================================================
# SYMBOLS
# ============================================================

def get_symbols(market):

    config = get_market_config(market)

    return config["symbols"]


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("US MARKET CONFIGURATION")
    print("=" * 60)

    config = get_market_config("US")

    symbols = get_symbols("US")

    print()
    print(f"Market:    {config['name']}")
    print(f"Currency:  {config['currency']}")
    print(
        f"Exchanges: {', '.join(config['exchanges'])}"
    )

    print()
    print(
        f"Stock universe: {len(symbols)} stocks"
    )

    print()
    print("Stocks:")

    for symbol in symbols:
        print(f"  - {symbol}")

    print()
    print("No orders were submitted.")