#!/usr/bin/env python3
"""
Stock Price Fetcher using Robinhood API

This script fetches the latest stock prices for tickers listed in an Excel file
using the robin_stocks library to connect to Robinhood.
"""

import robin_stocks.robinhood as r
import pandas as pd
import os
from typing import Dict, List, Any

# Configuration variables - can be set via environment variables or modified here
USERNAME = os.getenv("ROBINHOOD_USERNAME", "your_email")
PASSWORD = os.getenv("ROBINHOOD_PASSWORD", "your_password")
TICKERS_FILE = os.getenv("TICKERS_FILE", "tickers.xlsx")


def login_to_robinhood(username: str, password: str) -> bool:
    """
    Login to Robinhood with MFA support
    
    Args:
        username: Robinhood username/email
        password: Robinhood password
        
    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        # MFA code if enabled (Robinhood may text/email you)
        mfa_code = input("MFA Code (press Enter if no MFA): ").strip()
        if not mfa_code:
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


def fetch_stock_prices(tickers: List[str]) -> Dict[str, Any]:
    """
    Fetch latest prices for given tickers
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        Dictionary mapping ticker to price or error message
    """
    results = {}
    total_tickers = len(tickers)
    
    print(f"\n📈 Fetching prices for {total_tickers} tickers...")
    
    for i, ticker in enumerate(tickers, 1):
        try:
            price = r.stocks.get_latest_price(ticker)[0]
            results[ticker] = float(price) if price else "No price available"
            print(f"  {i}/{total_tickers} {ticker}: ${price}")
        except Exception as e:
            error_msg = f"Error: {e}"
            results[ticker] = error_msg
            print(f"  {i}/{total_tickers} {ticker}: {error_msg}")
    
    return results


def print_results(results: Dict[str, Any]) -> None:
    """
    Print formatted results
    
    Args:
        results: Dictionary of ticker to price/error mappings
    """
    print("\n" + "="*50)
    print("         CURRENT STOCK PRICES")
    print("="*50)
    
    for ticker, price in results.items():
        if isinstance(price, float):
            print(f"{ticker:>8}: ${price:>10.2f}")
        else:
            print(f"{ticker:>8}: {price}")
    
    print("="*50)


def main():
    """Main function to orchestrate the stock price fetching process"""
    print("🚀 Stock Price Fetcher - Robinhood Edition")
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
    
    # Step 3: Fetch latest prices
    results = fetch_stock_prices(tickers)
    
    # Step 4: Print results
    print_results(results)
    
    # Logout
    try:
        r.logout()
        print("\n✓ Logged out of Robinhood")
    except Exception as e:
        print(f"\n⚠️  Logout warning: {e}")


if __name__ == "__main__":
    main()