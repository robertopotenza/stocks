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


def fetch_stock_data(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch comprehensive stock data for given tickers
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        Dictionary mapping ticker to stock data dictionary containing:
        Price, 52w_High, 52w_Low, MarketCap, PE_Ratio
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
            'PE_Ratio': 'N/A'
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
            
            results[ticker] = stock_data
            print(f"  {i}/{total_tickers} {ticker}: ${stock_data['Price']}")
            
        except Exception as e:
            error_msg = f"Error: {e}"
            results[ticker] = {
                'Price': error_msg,
                '52w_High': 'N/A',
                '52w_Low': 'N/A', 
                'MarketCap': 'N/A',
                'PE_Ratio': 'N/A'
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
                'PE_Ratio': stock_data.get('PE_Ratio', 'N/A')
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
            
            if isinstance(price, (int, float)):
                print(f"{ticker:>8}: ${price:>10.2f} | 52w: ${high_52w:>8.2f}-${low_52w:>8.2f} | "
                      f"Cap: {market_cap:>12.0f} | P/E: {pe_ratio:>6.2f}")
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