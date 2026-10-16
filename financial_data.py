import requests

url = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"

headers = {
    "User-Agent": "AI Trading research@example.com"
}

response = requests.get(url, headers=headers)
response.raise_for_status()

data = response.json()
facts = data["facts"]["us-gaap"]


# =========================
# GET MOST RECENT QUARTER
# =========================

def latest_quarter(name):
    units = facts[name]["units"]
    unit = next(iter(units))

    entries = units[unit]

    # Keep entries that have a start date.
    # This lets us identify income/cash-flow reporting periods.
    entries = [
        x for x in entries
        if "start" in x and "end" in x
    ]

    # Prefer approximately 3-month periods
    quarterly = []

    for entry in entries:
        start = entry["start"]
        end = entry["end"]

        try:
            start_date = __import__("datetime").date.fromisoformat(start)
            end_date = __import__("datetime").date.fromisoformat(end)

            days = (end_date - start_date).days

            if 70 <= days <= 100:
                quarterly.append(entry)

        except ValueError:
            pass

    if not quarterly:
        return None

    # Most recently filed quarterly result
    quarterly.sort(
        key=lambda x: x.get("filed", "")
    )

    latest = quarterly[-1]

    return latest["val"], latest["start"], latest["end"], latest["filed"]


# =========================
# GET MOST RECENT BALANCE
# =========================

def latest_balance(name):
    units = facts[name]["units"]
    unit = next(iter(units))

    entries = [
        x for x in units[unit]
        if "end" in x and "start" not in x
    ]

    entries.sort(
        key=lambda x: x.get("filed", "")
    )

    latest = entries[-1]

    return latest["val"], latest["end"], latest["filed"]


# =========================
# QUARTERLY FINANCIAL DATA
# =========================

quarterly_metrics = {
    "Revenue": "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Net Income": "NetIncomeLoss",
    "Gross Profit": "GrossProfit",
    "Operating Income": "OperatingIncomeLoss",
    "Diluted EPS": "EarningsPerShareDiluted",
    "R&D Expense": "ResearchAndDevelopmentExpense",
}


# =========================
# BALANCE SHEET DATA
# =========================

balance_metrics = {
    "Cash": "CashAndCashEquivalentsAtCarryingValue",
    "Long-Term Debt": "LongTermDebt",
    "Total Assets": "Assets",
    "Total Liabilities": "Liabilities"
}


print("APPLE FINANCIAL DATA")
print("====================")
print()

print("LATEST QUARTER")
print("--------------")

for label, name in quarterly_metrics.items():
    result = latest_quarter(name)

    if result:
        value, start, end, filed = result

        print(
            f"{label}: {value} "
            f"(quarter {start} to {end}, filed {filed})"
        )

print()

print("LATEST BALANCE SHEET")
print("--------------------")

for label, name in balance_metrics.items():
    value, end, filed = latest_balance(name)

    print(
        f"{label}: {value} "
        f"(as of {end}, filed {filed})"
    )