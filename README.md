# Robinhood Stock Data Fetcher

A Python script that fetches comprehensive stock data from Robinhood for a list of tickers stored in an Excel file, then writes the results back to the Excel file with additional stock information.

## 🚀 Quick Start

**New to this application?** See **[GETTING_STARTED.md](GETTING_STARTED.md)** for a complete step-by-step setup guide!

**Quick Reference:**
- 📚 [Complete Setup Guide](GETTING_STARTED.md) - **Start here for first-time setup**
- 📁 [File Structure Guide](FILE_STRUCTURE.md) - Understand the project layout
- ⚡ Easy start: Run `./start.sh` (Linux/Mac) or `start.bat` (Windows)

**Quick Setup:**
```bash
# Easy setup script (Linux/Mac)
./start.sh

# Or manually:
pip install -r requirements.txt
export ROBINHOOD_USERNAME=your_email@example.com
export ROBINHOOD_PASSWORD=your_password
python3 main.py
```

## Features

- Fetches comprehensive stock data using the Robinhood API including:
  - Current stock price
  - 52-week high and low
  - Market capitalization 
  - P/E ratio
  - **Technical Analysis Levels (NEW!):**
    - **Pivot Point Support & Resistance**: Calculated using daily high, low, close prices
    - **Recent Support & Resistance**: Based on recent price action analysis over 20-day lookback period
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
- **Pivot_Support_1**: Primary pivot-based support level
- **Pivot_Support_2**: Secondary pivot-based support level
- **Pivot_Resistance_1**: Primary pivot-based resistance level
- **Pivot_Resistance_2**: Secondary pivot-based resistance level
- **Recent_Support**: Recent support level based on 20-day price action
- **Recent_Resistance**: Recent resistance level based on 20-day price action

## Usage

### Easy Start (Recommended)

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

### Manual Start

```bash
python stock_prices.py
# or
python main.py
```

The script will:
1. Prompt for your Robinhood credentials (if not set via environment variables)
2. Ask for MFA code if you have two-factor authentication enabled
3. Load ticker symbols from the Excel file
4. Fetch comprehensive stock data for each ticker (price, 52w high/low, market cap, P/E ratio)
5. **Calculate technical support and resistance levels using historical price data**
6. Write results back to the Excel file with new columns
7. Display formatted summary of results including technical levels

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
  1/8 AAPL: Calculating technical levels...
  1/8 AAPL: $150.25 | Sup: 147.83 | Res: 152.67
  2/8 GOOGL: Calculating technical levels...
  2/8 GOOGL: $2750.80 | Sup: 2685.42 | Res: 2816.18
  3/8 MSFT: Calculating technical levels...
  3/8 MSFT: $310.15 | Sup: 302.14 | Res: 318.16
  ...

✓ Results written to tickers.xlsx

======================================================================
         STOCK DATA SUMMARY
======================================================================
    AAPL: $    150.25 | 52w: $  199.62-$  124.17 | Cap: 2400000000000 | P/E:  28.50
          Pivot S/R: $147.83-$152.67 | Recent S/R: $145.20-$155.10
   GOOGL: $   2750.80 | 52w: $ 3030.93-$ 2193.62 | Cap: 1800000000000 | P/E:  25.20
          Pivot S/R: $2685.42-$2816.18 | Recent S/R: $2650.00-$2850.00
    MSFT: $    310.15 | 52w: $  384.30-$  247.11 | Cap: 2300000000000 | P/E:  31.80
          Pivot S/R: $302.14-$318.16 | Recent S/R: $295.50-$325.00
    TSLA: $    245.60 | 52w: $  414.50-$  152.37 | Cap: 780000000000  | P/E:  67.20
    AMZN: $   3200.75 | 52w: $ 3773.08-$ 2025.20 | Cap: 1650000000000 | P/E:  58.90
    META: $    325.60 | 52w: $  384.33-$  199.50 | Cap: 825000000000  | P/E:  24.80
    NVDA: $    450.30 | 52w: $  502.66-$  180.68 | Cap: 1120000000000 | P/E:  75.40
    NFLX: $    425.90 | 52w: $  485.76-$  271.56 | Cap: 189000000000  | P/E:  35.20
======================================================================

✓ Logged out of Robinhood
```

The Excel file (`tickers.xlsx`) will be updated with new columns containing the fetched data:

| Ticker | Price  | 52w_High | 52w_Low | MarketCap      | PE_Ratio | Pivot_Support_1 | Pivot_Resistance_1 | Recent_Support | Recent_Resistance |
|--------|--------|----------|---------|----------------|----------|-----------------|-------------------|----------------|-------------------|
| AAPL   | 150.25 | 199.62   | 124.17  | 2400000000000  | 28.5     | 147.83          | 152.67            | 145.20         | 155.10            |
| GOOGL  | 2750.80| 3030.93  | 2193.62 | 1800000000000  | 25.2     | 2685.42         | 2816.18           | 2650.00        | 2850.00           |
| ...    | ...    | ...      | ...     | ...            | ...      | ...             | ...               | ...            | ...               |

## Technical Analysis

The script now includes comprehensive technical analysis to identify support and resistance levels:

### Pivot Point Analysis
- **Pivot Point**: Calculated as (High + Low + Close) / 3 using the most recent trading day
- **Support Levels**: 
  - Support 1 = (2 × Pivot Point) - High
  - Support 2 = Pivot Point - (High - Low)
- **Resistance Levels**:
  - Resistance 1 = (2 × Pivot Point) - Low  
  - Resistance 2 = Pivot Point + (High - Low)

### Recent Price Action Analysis
- Analyzes the last 20 trading days of price data
- Identifies key support and resistance levels based on recent highs and lows
- Provides additional confirmation for trading decisions

### Data Requirements
- Uses 3 months of daily historical data for calculations
- Handles missing or insufficient data gracefully with 'N/A' values
- All calculations are performed using Robinhood's historical price data

## Railway Deployment

This repository is ready for deployment on Railway. Railway will automatically detect the `Procfile` and deploy this as a Worker service (no HTTP port exposed).

### Quick Deploy to Railway

1. **Deploy with Railway CLI** (recommended):
   ```bash
   npm install -g @railway/cli
   railway login
   railway init
   railway up
   ```

2. **Deploy via GitHub Integration**:
   - Connect your GitHub repository to Railway
   - Railway will automatically detect the `Procfile` and `Dockerfile`
   - Select "Worker" as the service type during setup

### Required Environment Variables

Set these environment variables in your Railway project:

- `ROBINHOOD_USERNAME`: Your Robinhood email/username
- `ROBINHOOD_PASSWORD`: Your Robinhood password  
- `TICKERS_FILE`: Set to `tickers.xlsx` if keeping the Excel file in the repository

### Database Storage (Optional)

If you need persistent storage for the `tickers.xlsx` file:

1. Add a database service to your Railway project (PostgreSQL/MySQL)
2. Use the provided database environment variables to connect
3. Modify the application to store ticker data in the database instead of Excel

### Railway Configuration Files

- `Dockerfile`: Containerizes the application for Railway
- `Procfile`: Specifies this as a Worker service (`worker: python main.py`)

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
