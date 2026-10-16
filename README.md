# AI Alpaca Trader

An AI-powered Python trading bot that uses your own AI API to analyze US stocks and execute simulated trades through Alpaca.

Configure your own AI API and Alpaca paper-trading credentials to let the AI analyze market data, research companies, and make trading decisions.

> [!WARNING]
> **PAPER TRADING ONLY — NO REAL-MONEY TRADING IS ENABLED IN THIS VERSION.**
>
> This project is intended for simulated trading using an Alpaca paper-trading account. Always verify the configuration and source code before running it.

## Features

- **AI-powered analysis** — Uses your own AI API to help evaluate stocks and make trading decisions.
- **US stock market** — Focuses on US-listed stocks.
- **Alpaca integration** — Uses Alpaca for market data and simulated trade execution.
- **Company research** — Includes modules for financial data, historical prices, stock screening, and company information.
- **Portfolio management** — Considers available cash and existing positions when making trading decisions.
- **Risk controls** — Designed to prevent short selling and leverage.
- **Automated operation** — Can run periodically to check market conditions and analyze potential trades.
- **Customizable configuration** — Adjust the stock universe, analysis interval, and other settings to suit your testing needs.

## How It Works

1. Collects market and historical stock data.
2. Retrieves relevant financial information and company research.
3. Sends relevant information to an AI model for analysis.
4. Receives a proposed BUY, HOLD, or SELL decision.
5. Applies the bot's validation and risk checks.
6. Sends eligible orders to the Alpaca paper-trading account.

AI-generated decisions are not guaranteed to be accurate or profitable. Review the code and test the system before relying on its output.

## Requirements

- Python 3.12 or a compatible Python version.
- An OpenAI API key or compatible AI API configuration supported by the code.
- An Alpaca paper-trading account and paper API credentials.
- The Python packages listed in `requirements.txt` (if provided).

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/ai-alpaca-trader.git
cd ai-alpaca-trader
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

If the repository contains a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Otherwise, install the required dependencies specified by the project source code.

### 4. Configure API credentials

Create a local `.env` file using the variable names expected by the project.

Typical credentials include:

```env
OPENAI_API_KEY=your_ai_api_key
ALPACA_API_KEY=your_alpaca_paper_api_key
ALPACA_SECRET_KEY=your_alpaca_paper_secret_key
```

**Important:** These variable names are examples. Check the source code for the exact names your version expects.

Use paper-trading credentials only. Never commit `.env` or expose API keys, secret keys, or account credentials on GitHub.

### 5. Review the configuration

Before starting the bot, verify:

- The Alpaca endpoint is configured for paper trading.
- Live trading is not enabled.
- The AI API settings and stock universe are correct.
- Risk checks and order validation are enabled.
- Your API usage and costs are appropriate for your testing.

### 6. Run the bot

Check `trading_bot.py` and the project instructions for the correct startup command. For example:

```bash
python trading_bot.py
```

## Project Structure

| File | Purpose |
|---|---|
| `trading_bot.py` | Main trading bot loop |
| `ai_analysis.py` | AI-based stock analysis and decisions |
| `risk_manager.py` | Trading and risk validation |
| `order_engine.py` | Order execution logic |
| `market_data.py` | Market data retrieval |
| `historical_data.py` | Historical stock data |
| `financial_data.py` | Financial information |
| `stock_screener.py` | Stock screening |
| `market_config.py` | Market and stock universe configuration |
| `market_hours.py` | Market-hours logic |
| `sec_company_lookup.py` | Company lookup utilities |
| `trading_config.py` | Trading configuration |

Some optional scripts are used for testing and order management.

## AI Assistance Disclosure

This project was developed with assistance from AI tools, including help with code generation, debugging, documentation, and development guidance. The project author is responsible for reviewing, testing, and maintaining the published code.

## Disclaimer

This project is provided for educational and experimental purposes only. It is not financial advice, and it does not guarantee profits or prevent losses.

AI-generated analysis may be incorrect, incomplete, or based on outdated information. Paper-trading results do not guarantee future performance in live markets.

Use at your own risk and verify all configurations before execution.

## License

No license has been specified yet. Unless a license is added, the repository should not be assumed to grant permission for others to reuse, modify, or redistribute the code.
