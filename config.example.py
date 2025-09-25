# Robinhood Stock Price Fetcher Configuration
# Copy this file to config.py and update with your credentials

# Robinhood Login Credentials
# You can also set these as environment variables:
# export ROBINHOOD_USERNAME=your_email@example.com
# export ROBINHOOD_PASSWORD=your_password

ROBINHOOD_USERNAME = "your_email"
ROBINHOOD_PASSWORD = "your_password"

# Twelve Data API Key for technical indicators and current prices
# Get your free API key from https://twelvedata.com/
# Set as environment variable: export TWELVEDATA_API_KEY=your_api_key
TWELVEDATA_API_KEY = "your_twelvedata_api_key"

# Optional: Override Twelve Data rate limiting defaults (free tier: 8 req/min)
# export TWELVEDATA_REQUESTS_PER_MINUTE=8
# export TWELVEDATA_COOLDOWN_SECONDS=15
# TWELVEDATA_REQUESTS_PER_MINUTE = 8
# TWELVEDATA_COOLDOWN_SECONDS = 15

# Path to Excel file containing tickers (must have 'Ticker' column)
TICKERS_FILE = "tickers.xlsx"