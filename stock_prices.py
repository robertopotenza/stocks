#!/usr/bin/env python3
"""
Stock Data Fetcher using Robinhood API

This script fetches comprehensive stock data for tickers listed in an Excel file
using the robin_stocks library to connect to Robinhood. It retrieves current price,
52-week high/low, market capitalization, and P/E ratio, then writes the results
back to the Excel file.
"""

import robin_stocks.robinhood as r
import pandas as pd
import os
import sys
from typing import Dict, List, Any
from technical_analysis import calculate_technical_levels

# Configuration variables - can be set via environment variables or modified here
USERNAME = os.getenv("ROBINHOOD_USERNAME", "your_email")
PASSWORD = os.getenv("ROBINHOOD_PASSWORD", "your_password")
TICKERS_FILE = os.getenv("TICKERS_FILE", "tickers.xlsx")


def login_to_robinhood(username: str, password: str) -> bool:
    """
    Login to Robinhood with optional non-interactive MFA support.

    If ROBINHOOD_MFA environment variable is set, it will be used.
    Otherwise the function will prompt for MFA (interactive) only if running
    in an interactive environment.
    """
    try:
        # Try to get MFA code from environment first (non-interactive)
        mfa_code = os.getenv("ROBINHOOD_MFA")
        if mfa_code:
            mfa_code = mfa_code.strip() or None
        else:
            # Check if we're in an interactive environment
            # Robust headless/containerized environment detection
            def is_docker_environment():
                """Detect if running in Docker container."""
                # Check for /.dockerenv file (most reliable)
                if os.path.exists("/.dockerenv"):
                    return True
                # Check cgroup for docker container info
                try:
                    with open("/proc/1/cgroup", "r") as f:
                        return "docker" in f.read()
                except (OSError, IOError):
                    pass
                return False

            is_interactive = (
                sys.stdin.isatty() and
                sys.stdout.isatty() and
                os.getenv("TERM") is not None and
                not os.getenv("CI") and  # Not in CI environment
                not is_docker_environment()  # Not in Docker
            )
            if is_interactive:
                # interactive fallback (only available on interactive platforms)
                try:
                    mfa_code = input("MFA Code (press Enter if no MFA): ").strip()
                    if not mfa_code:
                        mfa_code = None
                except Exception:
                    # If input() isn't available, proceed without MFA (may fail)
                    mfa_code = None
            else:
                # In headless environment, skip MFA prompt and proceed without it
                print("ℹ️  Running in headless environment - skipping MFA prompt")
                print("   Set ROBINHOOD_MFA environment variable if MFA is required")
                mfa_code = None

        login = r.login(username, password, mfa_code=mfa_code)

        if login:
            print("✓ Successfully logged into Robinhood")
            return True
        else:
            print("✗ Failed to login to Robinhood")
            return False
    except Exception as e:
        print(f"✗ Login error: {e}")
        return False


def load_tickers_from_excel(file_path: str) -> List[str]:
    """
    Load ticker symbols from Excel file
    
    Args:
        file_path: Path to Excel file with 'Ticker' column
        
    Returns:
        List of ticker symbols
    """
    try:
        # Make sure tickers.xlsx has a column called 'Ticker'
        df = pd.read_excel(file_path)
        
        if 'Ticker' not in df.columns:
            raise ValueError("Excel file must have a 'Ticker' column")
            
        tickers = df["Ticker"].dropna().tolist()
        print(f"✓ Loaded {len(tickers)} tickers from {file_path}")
        return tickers
    except Exception as e:
        print(f"✗ Error loading tickers from {file_path}: {e}")
        return []


def fetch_stock_data(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch comprehensive stock data for given tickers
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        Dictionary mapping ticker to stock data dictionary containing:
        Price, 52w_High, 52w_Low, MarketCap, PE_Ratio, and Technical Levels
    """
    results = {}
    total_tickers = len(tickers)
    
    print(f"\n📈 Fetching stock data for {total_tickers} tickers...")
    
    for i, ticker in enumerate(tickers, 1):
        stock_data = {
            'Price': 'N/A',
            '52w_High': 'N/A', 
            '52w_Low': 'N/A',
            'MarketCap': 'N/A',
            'PE_Ratio': 'N/A',
            'Pivot_Support_1': 'N/A',
            'Pivot_Support_2': 'N/A',
            'Pivot_Resistance_1': 'N/A',
            'Pivot_Resistance_2': 'N/A',
            'Recent_Support': 'N/A',
            'Recent_Resistance': 'N/A'
        }
        
        try:
            # Get current price from quotes
            quote_data = r.stocks.get_quotes(ticker)
            if quote_data and len(quote_data) > 0:
                price = quote_data[0].get('last_trade_price')
                if price:
                    stock_data['Price'] = float(price)
            
            # Get fundamentals data
            fundamental_data = r.stocks.get_fundamentals(ticker)
            if fundamental_data and len(fundamental_data) > 0:
                fund = fundamental_data[0]
                
                # 52-week high
                high_52w = fund.get('high_52_weeks')
                if high_52w:
                    stock_data['52w_High'] = float(high_52w)
                
                # 52-week low
                low_52w = fund.get('low_52_weeks')
                if low_52w:
                    stock_data['52w_Low'] = float(low_52w)
                
                # Market cap
                market_cap = fund.get('market_cap')
                if market_cap:
                    stock_data['MarketCap'] = float(market_cap)
                
                # P/E ratio
                pe_ratio = fund.get('pe_ratio')
                if pe_ratio:
                    stock_data['PE_Ratio'] = float(pe_ratio)
            
            # Calculate technical levels (Support & Resistance)
            print(f"  {i}/{total_tickers} {ticker}: Calculating technical levels...")
            technical_levels = calculate_technical_levels(ticker)
            
            # Add technical analysis results
            stock_data.update({
                'Pivot_Support_1': technical_levels.get('pivot_support_1', 'N/A'),
                'Pivot_Support_2': technical_levels.get('pivot_support_2', 'N/A'),
                'Pivot_Resistance_1': technical_levels.get('pivot_resistance_1', 'N/A'),
                'Pivot_Resistance_2': technical_levels.get('pivot_resistance_2', 'N/A'),
                'Recent_Support': technical_levels.get('recent_support', 'N/A'),
                'Recent_Resistance': technical_levels.get('recent_resistance', 'N/A')
            })
            
            results[ticker] = stock_data
            print(f"  {i}/{total_tickers} {ticker}: ${stock_data['Price']} | "
                  f"Sup: {stock_data['Pivot_Support_1']} | Res: {stock_data['Pivot_Resistance_1']}")
            
        except Exception as e:
            error_msg = f"Error: {e}"
            results[ticker] = {
                'Price': error_msg,
                '52w_High': 'N/A',
                '52w_Low': 'N/A', 
                'MarketCap': 'N/A',
                'PE_Ratio': 'N/A',
                'Pivot_Support_1': 'N/A',
                'Pivot_Support_2': 'N/A',
                'Pivot_Resistance_1': 'N/A',
                'Pivot_Resistance_2': 'N/A',
                'Recent_Support': 'N/A',
                'Recent_Resistance': 'N/A'
            }
            print(f"  {i}/{total_tickers} {ticker}: {error_msg}")
    
    return results


def write_results_to_excel(tickers: List[str], results: Dict[str, Dict[str, Any]], file_path: str) -> None:
    """
    Write stock data results back to Excel file
    
    Args:
        tickers: List of original ticker symbols
        results: Dictionary of ticker to stock data mappings
        file_path: Path to Excel file to write results to
    """
    def safe_format_float(value, format_spec: str) -> str:
        """Safely format a value as float, returning 'N/A' for non-numeric values"""
        if isinstance(value, (int, float)) and value != 'N/A':
            try:
                return f"{value:{format_spec}}"
            except (ValueError, TypeError):
                return 'N/A'
        else:
            return 'N/A'
    
    def safe_format_price(value) -> str:
        """Safely format a price value"""
        return safe_format_float(value, '>10.2f')
    
    def safe_format_number(value, format_spec: str) -> str:
        """Safely format a number value"""
        return safe_format_float(value, format_spec)
    
    try:
        # Create DataFrame with all data
        data_rows = []
        for ticker in tickers:
            stock_data = results.get(ticker, {})
            row = {
                'Ticker': ticker,
                'Price': stock_data.get('Price', 'N/A'),
                '52w_High': stock_data.get('52w_High', 'N/A'),
                '52w_Low': stock_data.get('52w_Low', 'N/A'),
                'MarketCap': stock_data.get('MarketCap', 'N/A'),
                'PE_Ratio': stock_data.get('PE_Ratio', 'N/A'),
                'Pivot_Support_1': stock_data.get('Pivot_Support_1', 'N/A'),
                'Pivot_Support_2': stock_data.get('Pivot_Support_2', 'N/A'),
                'Pivot_Resistance_1': stock_data.get('Pivot_Resistance_1', 'N/A'),
                'Pivot_Resistance_2': stock_data.get('Pivot_Resistance_2', 'N/A'),
                'Recent_Support': stock_data.get('Recent_Support', 'N/A'),
                'Recent_Resistance': stock_data.get('Recent_Resistance', 'N/A')
            }
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Write to Excel using openpyxl engine
        df.to_excel(file_path, engine='openpyxl', index=False)
        
        print(f"\n✓ Results written to {file_path}")
        
        # Print summary for user
        print("\n" + "="*70)
        print("         STOCK DATA SUMMARY")
        print("="*70)
        
        for _, row in df.iterrows():
            ticker = row['Ticker']
            price = row['Price']
            high_52w = row['52w_High']
            low_52w = row['52w_Low']
            market_cap = row['MarketCap']
            pe_ratio = row['PE_Ratio']
            pivot_sup1 = row['Pivot_Support_1']
            pivot_res1 = row['Pivot_Resistance_1']
            recent_sup = row['Recent_Support']
            recent_res = row['Recent_Resistance']
            
            if isinstance(price, (int, float)):
                print(f"{ticker:>8}: ${safe_format_price(price)} | "
                      f"52w: ${safe_format_number(high_52w, '>8.2f')}-${safe_format_number(low_52w, '>8.2f')} | "
                      f"Cap: {safe_format_number(market_cap, '>12.0f')} | "
                      f"P/E: {safe_format_number(pe_ratio, '>6.2f')}")
                print(f"{'':>8}  Pivot S/R: {safe_format_number(pivot_sup1, '.2f')}-{safe_format_number(pivot_res1, '.2f')} | "
                      f"Recent S/R: {safe_format_number(recent_sup, '.2f')}-{safe_format_number(recent_res, '.2f')}")
            else:
                print(f"{ticker:>8}: {str(price):>12} | Data: N/A")
        
        print("="*70)
        
    except Exception as e:
        print(f"✗ Error writing results to Excel: {e}")
        # Fall back to printing results
        print("\n" + "="*50)
        print("         STOCK DATA (Excel write failed)")
        print("="*50)
        for ticker, data in results.items():
            print(f"{ticker}: {data}")
        print("="*50)


def main():
    """Main function to orchestrate the stock price fetching process"""
    print("🚀 Stock Data Fetcher - Robinhood Edition")
    print("="*50)
    
    # Check if credentials are set
    if USERNAME == "your_email" or PASSWORD == "your_password":
        print("⚠️  Warning: Please set your Robinhood credentials!")
        print("   Set ROBINHOOD_USERNAME and ROBINHOOD_PASSWORD environment variables")
        print("   or modify the USERNAME and PASSWORD variables in this script.")
        print("\nExample:")
        print("   export ROBINHOOD_USERNAME=your_email@example.com")
        print("   export ROBINHOOD_PASSWORD=your_password")
        return
    
    # Step 1: Login to Robinhood
    print(f"\n🔐 Logging into Robinhood as {USERNAME}...")
    if not login_to_robinhood(USERNAME, PASSWORD):
        return
    
    # Step 2: Load Excel tickers
    print(f"\n📊 Loading tickers from {TICKERS_FILE}...")
    tickers = load_tickers_from_excel(TICKERS_FILE)
    if not tickers:
        return
    
    # Step 3: Fetch comprehensive stock data
    results = fetch_stock_data(tickers)
    
    # Step 4: Write results to Excel
    write_results_to_excel(tickers, results, TICKERS_FILE)
    
    # Logout
    try:
        r.logout()
        print("\n✓ Logged out of Robinhood")
    except Exception as e:
        print(f"\n⚠️  Logout warning: {e}")


if __name__ == "__main__":
    main()