# Robinhood Stock Price Fetcher

A Python script that fetches current stock prices from Robinhood for a list of tickers stored in an Excel file.

## Features

- Fetches real-time stock prices using the Robinhood API
- Reads ticker symbols from Excel file
- Supports Multi-Factor Authentication (MFA)
- Configurable credentials via environment variables or script modification
- Error handling for invalid tickers or API issues
- Clean, formatted output

## Requirements

- Python 3.6+
- Robinhood account
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

### Method 1: Environment Variables (Recommended)
```bash
export ROBINHOOD_USERNAME=your_email@example.com
export ROBINHOOD_PASSWORD=your_password
```

### Method 2: Configuration File
1. Copy the example configuration:
   ```bash
   cp config.example.py config.py
   ```
2. Edit `config.py` with your credentials

### Method 3: Direct Script Modification
Edit the `USERNAME` and `PASSWORD` variables at the top of `stock_prices.py`

## Prepare Your Ticker List

The script reads ticker symbols from an Excel file named `tickers.xlsx` (configurable). The file must have a column named 'Ticker'.

A sample file is included with popular stocks: AAPL, GOOGL, MSFT, TSLA, AMZN, META, NVDA, NFLX

To create your own:
1. Create an Excel file with a 'Ticker' column
2. List your desired stock symbols (e.g., AAPL, MSFT, GOOGL)
3. Save as `tickers.xlsx` or update the `TICKERS_FILE` variable

## Usage

Run the script:
```bash
python stock_prices.py
```

The script will:
1. Prompt for your Robinhood credentials (if not set via environment variables)
2. Ask for MFA code if you have two-factor authentication enabled
3. Load ticker symbols from the Excel file
4. Fetch current prices for each ticker
5. Display formatted results

## Example Output

```
🚀 Stock Price Fetcher - Robinhood Edition
==================================================

🔐 Logging into Robinhood as your_email@example.com...
MFA Code (press Enter if no MFA): 
✓ Successfully logged into Robinhood

📊 Loading tickers from tickers.xlsx...
✓ Loaded 8 tickers from tickers.xlsx

📈 Fetching prices for 8 tickers...
  1/8 AAPL: $150.25
  2/8 GOOGL: $2,750.80
  3/8 MSFT: $310.15
  ...

==================================================
         CURRENT STOCK PRICES
==================================================
    AAPL: $    150.25
   GOOGL: $  2,750.80
    MSFT: $    310.15
    TSLA: $    250.40
    AMZN: $  3,200.75
    META: $    325.60
    NVDA: $    450.30
    NFLX: $    425.90
==================================================

✓ Logged out of Robinhood
```

## Security Notes

- Never commit your actual credentials to version control
- Use environment variables for sensitive information
- Consider using a `.env` file with python-dotenv for local development
- Always log out when finished to maintain security

## Troubleshooting

1. **Login Issues**: Ensure your credentials are correct and MFA code is entered if prompted
2. **Missing Tickers**: Check that your Excel file has a 'Ticker' column with valid stock symbols
3. **API Errors**: Some tickers might not be available through Robinhood's API
4. **Rate Limiting**: If fetching many tickers, you might encounter rate limits

## License

This project is provided as-is for educational purposes. Please ensure compliance with Robinhood's Terms of Service.
