import requests


# ============================================================
# SEC COMPANY LOOKUP
# ============================================================

SEC_URL = (
    "https://www.sec.gov/files/"
    "company_tickers.json"
)

SEC_USER_AGENT = (
    "AI Trading research@example.com"
)


def get_sec_company_tickers():

    response = requests.get(
        SEC_URL,
        headers={
            "User-Agent": SEC_USER_AGENT
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def build_ticker_lookup():

    data = get_sec_company_tickers()

    lookup = {}

    for company in data.values():

        ticker = company.get(
            "ticker"
        )

        cik = company.get(
            "cik_str"
        )

        if not ticker or cik is None:
            continue

        lookup[ticker.upper()] = (
            str(cik).zfill(10)
        )

    return lookup


if __name__ == "__main__":

    print("=" * 60)
    print("SEC COMPANY TICKER LOOKUP")
    print("=" * 60)

    lookup = build_ticker_lookup()

    print()
    print(
        f"SEC companies loaded: "
        f"{len(lookup)}"
    )

    print()

    test_symbols = [
        "AAPL",
        "MSFT",
        "NVDA",
        "GOOGL",
        "AMZN",
        "MU",
        "MRK",
        "COP",
        "XOM",
        "PANW"
    ]

    print("Test tickers:")

    for symbol in test_symbols:

        cik = lookup.get(symbol)

        if cik:

            print(
                f"  {symbol}: CIK {cik}"
            )

        else:

            print(
                f"  {symbol}: NOT FOUND"
            )

    print()
    print(
        "No orders were submitted."
    )