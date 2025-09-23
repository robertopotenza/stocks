# Getting Started with Robinhood Stock Data Fetcher

This guide will walk you through setting up and running the Robinhood Stock Data Fetcher application step by step.

## Prerequisites

- Python 3.12+ installed on your system
- A Robinhood account with login credentials
- pip (Python package manager)

## Step-by-Step Setup Guide

### Step 1: Verify Your Environment

1. **Check Python Version**
   ```bash
   python3 --version
   ```
   Should show Python 3.12 or higher.

2. **Check pip Installation**
   ```bash
   pip --version
   ```

### Step 2: Install Dependencies

Navigate to the project directory and install required packages:

```bash
cd /path/to/stocks
pip install -r requirements.txt
```

This will install:
- `robin-stocks>=3.0.0` - Robinhood API client
- `pandas>=1.3.0` - Data manipulation and Excel handling
- `openpyxl>=3.0.0` - Excel file read/write support

### Step 3: Configure Your Credentials

You have **3 options** to set up your Robinhood credentials:

#### Option A: Environment Variables (Recommended for Security)

**Linux/Mac:**
```bash
export ROBINHOOD_USERNAME=your_email@example.com
export ROBINHOOD_PASSWORD=your_password
```

**Windows Command Prompt:**
```cmd
set ROBINHOOD_USERNAME=your_email@example.com
set ROBINHOOD_PASSWORD=your_password
```

**Windows PowerShell:**
```powershell
$env:ROBINHOOD_USERNAME = "your_email@example.com"
$env:ROBINHOOD_PASSWORD = "your_password"
```

#### Option B: Configuration File

1. Copy the example configuration:
   ```bash
   cp config.example.py config.py
   ```

2. Edit `config.py` with your credentials:
   ```python
   ROBINHOOD_USERNAME = "your_email@example.com"
   ROBINHOOD_PASSWORD = "your_password"
   ```

3. Modify `stock_prices.py` to import from config:
   ```python
   try:
       from config import ROBINHOOD_USERNAME, ROBINHOOD_PASSWORD
       USERNAME = ROBINHOOD_USERNAME
       PASSWORD = ROBINHOOD_PASSWORD
   except ImportError:
       USERNAME = os.getenv("ROBINHOOD_USERNAME", "your_email")
       PASSWORD = os.getenv("ROBINHOOD_PASSWORD", "your_password")
   ```

#### Option C: Direct Script Modification (Least Secure)

Edit the variables at the top of `stock_prices.py`:
```python
USERNAME = "your_email@example.com"
PASSWORD = "your_password"
```

⚠️ **Warning**: Never commit actual credentials to version control!

### Step 4: Prepare Your Stock List

The application reads stock tickers from `tickers.xlsx`. The provided file already contains 212 popular stocks.

**To customize your stock list:**

1. Open `tickers.xlsx` in Excel or any spreadsheet application
2. Modify the 'Ticker' column with your desired stock symbols
3. Save the file

**Required format:**
- Must have a column named 'Ticker'
- Each row should contain a valid stock symbol (e.g., AAPL, MSFT, GOOGL)

### Step 5: Run the Application

#### Basic Run

```bash
python3 main.py
```

#### Alternative Entry Points

```bash
# Direct execution
python3 stock_prices.py

# With environment variables inline
ROBINHOOD_USERNAME=your_email@example.com ROBINHOOD_PASSWORD=your_password python3 main.py
```

### Step 6: Handle Multi-Factor Authentication (MFA)

If your Robinhood account has MFA enabled:

1. When prompted, enter your MFA code:
   ```
   MFA Code (press Enter if no MFA): 123456
   ```

2. If no MFA is setup, just press Enter

### Step 7: Review Results

After successful execution:

1. **Console Output**: Shows progress and summary of fetched data
2. **Excel File**: Updated `tickers.xlsx` with new columns:
   - Price
   - 52w_High, 52w_Low
   - MarketCap
   - PE_Ratio
   - Pivot_Support_1, Pivot_Support_2
   - Pivot_Resistance_1, Pivot_Resistance_2
   - Recent_Support, Recent_Resistance

## Example Output

```
🚀 Stock Data Fetcher - Robinhood Edition
==================================================

🔐 Logging into Robinhood as your_email@example.com...
MFA Code (press Enter if no MFA): 
✓ Successfully logged into Robinhood

📊 Loading tickers from tickers.xlsx...
✓ Loaded 212 tickers from tickers.xlsx

📈 Fetching stock data for 212 tickers...
  1/212 AAGIY: Calculating technical levels...
  1/212 AAGIY: $15.25 | Sup: 14.83 | Res: 15.67
  2/212 AAPL: Calculating technical levels...
  2/212 AAPL: $150.25 | Sup: 147.83 | Res: 152.67
  ...

✓ Results written to tickers.xlsx
✓ Logged out of Robinhood
```

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'robin_stocks'"**
   - Solution: Run `pip install -r requirements.txt`

2. **"Warning: Please set your Robinhood credentials!"**
   - Solution: Configure credentials using one of the methods above

3. **Login failures**
   - Check credentials are correct
   - Ensure MFA code is entered if prompted
   - Try logging into Robinhood website first to verify account status

4. **"No tickers found" or Excel errors**
   - Ensure `tickers.xlsx` exists and has a 'Ticker' column
   - Check file permissions
   - Verify Excel file is not open in another application

5. **Rate limiting issues**
   - The app includes delays between requests
   - For large ticker lists, consider running in smaller batches

### Debug Mode

To see more detailed output, you can modify the script to add debug logging.

### Support

- Check the main README.md for additional documentation
- Review TECHNICAL_ANALYSIS.md for details on technical indicators
- Ensure compliance with Robinhood's Terms of Service

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for production deployments
3. **Log out properly** when finished (the app does this automatically)
4. **Keep dependencies updated** regularly

## Next Steps

- Review the generated Excel file with your stock data
- Customize the ticker list for your specific needs
- Consider setting up automated runs using cron/scheduled tasks
- Explore deployment options using Docker or Railway (see README.md)

---

**Happy Trading! 📈**