# Robinhood Stock Data Fetcher

A Python script that fetches comprehensive stock data from Robinhood for a list of tickers stored in an Excel file, then writes the results back to the Excel file with additional stock information.

## Features

- Fetches comprehensive stock data using the Robinhood API including:
  - Current stock price
  - 52-week high and low
  - Market capitalization 
  - P/E ratio
- Reads ticker symbols from Excel file
- Writes results back to Excel file with new columns
- Supports Multi-Factor Authentication (MFA)
- Configurable credentials via environment variables or script modification
- Error handling for invalid tickers or API issues with 'N/A' fallback values
- Uses openpyxl engine for Excel operations
- Clean, formatted console output and Excel results

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

After running the script, the Excel file will be updated with additional columns:
- **Price**: Current stock price
- **52w_High**: 52-week high price
- **52w_Low**: 52-week low price  
- **MarketCap**: Market capitalization
- **PE_Ratio**: Price-to-earnings ratio

## Usage

Run the script:
```bash
python stock_prices.py
```

The script will:
1. Prompt for your Robinhood credentials (if not set via environment variables)
2. Ask for MFA code if you have two-factor authentication enabled
3. Load ticker symbols from the Excel file
4. Fetch comprehensive stock data for each ticker (price, 52w high/low, market cap, P/E ratio)
5. Write results back to the Excel file with new columns
6. Display formatted summary of results

## Example Output

```
🚀 Stock Data Fetcher - Robinhood Edition
==================================================

🔐 Logging into Robinhood as your_email@example.com...
MFA Code (press Enter if no MFA): 
✓ Successfully logged into Robinhood

📊 Loading tickers from tickers.xlsx...
✓ Loaded 8 tickers from tickers.xlsx

📈 Fetching stock data for 8 tickers...
  1/8 AAPL: $150.25
  2/8 GOOGL: $2750.80
  3/8 MSFT: $310.15
  ...

✓ Results written to tickers.xlsx

======================================================================
         STOCK DATA SUMMARY
======================================================================
    AAPL: $    150.25 | 52w: $  199.62-$  124.17 | Cap: 2400000000000 | P/E:  28.50
   GOOGL: $   2750.80 | 52w: $ 3030.93-$ 2193.62 | Cap: 1800000000000 | P/E:  25.20
    MSFT: $    310.15 | 52w: $  384.30-$  247.11 | Cap: 2300000000000 | P/E:  31.80
    TSLA: $    245.60 | 52w: $  414.50-$  152.37 | Cap: 780000000000  | P/E:  67.20
    AMZN: $   3200.75 | 52w: $ 3773.08-$ 2025.20 | Cap: 1650000000000 | P/E:  58.90
    META: $    325.60 | 52w: $  384.33-$  199.50 | Cap: 825000000000  | P/E:  24.80
    NVDA: $    450.30 | 52w: $  502.66-$  180.68 | Cap: 1120000000000 | P/E:  75.40
    NFLX: $    425.90 | 52w: $  485.76-$  271.56 | Cap: 189000000000  | P/E:  35.20
======================================================================

✓ Logged out of Robinhood
```

The Excel file (`tickers.xlsx`) will be updated with new columns containing the fetched data:

| Ticker | Price  | 52w_High | 52w_Low | MarketCap      | PE_Ratio |
|--------|--------|----------|---------|----------------|----------|
| AAPL   | 150.25 | 199.62   | 124.17  | 2400000000000  | 28.5     |
| GOOGL  | 2750.80| 3030.93  | 2193.62 | 1800000000000  | 25.2     |
| ...    | ...    | ...      | ...     | ...            | ...      |

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
