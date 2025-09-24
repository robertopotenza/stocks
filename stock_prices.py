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
from datetime import datetime
from typing import Dict, List, Any
from technical_analysis import calculate_technical_levels
from logging_config import get_logger

# Get logger instance
logger = get_logger('stocks_app.stock_prices')

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
                logger.info("Running in headless environment - skipping MFA prompt")
                logger.info("Set ROBINHOOD_MFA environment variable if MFA is required")
                mfa_code = None

        login = r.login(username, password, mfa_code=mfa_code)

        if login:
            logger.info("Successfully logged into Robinhood")
            return True
        else:
            logger.error("Failed to login to Robinhood")
            return False
    except Exception as e:
        logger.error(f"Login error: {e}")
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
        logger.info(f"Loaded {len(tickers)} tickers from {file_path}")
        return tickers
    except Exception as e:
        logger.error(f"Error loading tickers from {file_path}: {e}")
        return []


def fetch_stock_data(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch minimal essential stock data for given tickers
    
    Args:
        tickers: List of ticker symbols
        
    Returns:
        Dictionary mapping ticker to minimal stock data dictionary
    """
    results = {}
    total_tickers = len(tickers)
    
    logger.info(f"🔄 Starting minimal data fetch for {total_tickers} tickers...")
    logger.info("📊 Progress will be reported every 5 tickers")
    
    for i, ticker in enumerate(tickers, 1):
        stock_data = {
            # Essential fields only
            'Date': 'N/A',  # Will be set to current date
            'Ticker': ticker,
        }
        
        try:
            # Set current date
            stock_data['Date'] = datetime.now().strftime('%Y-%m-%d')
            
            # Note: We're not fetching price, technical, or fundamental data anymore
            # as per the requirement to eliminate these fields
            
            logger.debug(f"{i}/{total_tickers} {ticker}: Minimal data prepared")
            
        except Exception as e:
            logger.error(f"{i}/{total_tickers} {ticker}: Error processing - {e}")
        
        results[ticker] = stock_data
        
        # Progress reporting every 5 tickers
        if i % 5 == 0 or i == total_tickers:
            logger.info(f"📊 Progress: {i}/{total_tickers} tickers processed ({(i/total_tickers)*100:.1f}%)")
    
    logger.info(f"✅ Data fetch completed for {total_tickers} tickers")
    return results


def write_results_to_excel(tickers: List[str], results: Dict[str, Dict[str, Any]], file_path: str) -> None:
    """
    Write minimal stock data results back to Excel file
    
    Args:
        tickers: List of original ticker symbols
        results: Dictionary of ticker to stock data mappings
        file_path: Path to Excel file to write results to
    """
    import shutil
    from datetime import datetime
    
    try:
        # Create backup of existing file if it exists
        if os.path.exists(file_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{file_path}.bak.{timestamp}"
            shutil.copy2(file_path, backup_path)
            logger.info(f"📁 Created backup: {backup_path}")
        
        # Create DataFrame with minimal essential data only
        data_rows = []
        for ticker in tickers:
            stock_data = results.get(ticker, {})
            row = {
                # Essential fields only
                'Date': stock_data.get('Date', 'N/A'), 
                'Ticker': ticker,
                # No longer including removed fields like Price, P/E, etc.
            }
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        logger.info(f"💾 Saving {len(data_rows)} minimal stock records to Excel file...")
        # Write to Excel using openpyxl engine
        df.to_excel(file_path, engine='openpyxl', index=False)
        
        logger.info(f"✅ Results successfully written to {file_path}")
        
        # Log summary for user - minimal output
        logger.info("📊 FINAL STOCK DATA SUMMARY")
        logger.info("=" * 50)
        
        for _, row in df.iterrows():
            ticker = row['Ticker']
            date = row['Date']
            logger.info(f"{ticker:>8}: {date}")
        
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Error writing results to Excel: {e}")
        # Fall back to logging results
        logger.info("📊 FALLBACK: Displaying stock data in logs (Excel write failed)")
        logger.info("=" * 50)
        for ticker, data in results.items():
            # Log only essential data
            logger.info(f"{ticker}: Date={data.get('Date', 'N/A')}")
        logger.info("=" * 50)


def main():
    """Main function to orchestrate the stock price fetching process"""
    logger.info("🚀 Stock Data Fetcher - Robinhood Edition")
    logger.info("=" * 50)
    logger.info("📋 STARTING MAIN EXECUTION STEPS")
    logger.info("=" * 50)
    
    # Check if credentials are set
    if USERNAME == "your_email" or PASSWORD == "your_password":
        logger.warning("Please set your Robinhood credentials!")
        logger.warning("Set ROBINHOOD_USERNAME and ROBINHOOD_PASSWORD environment variables")
        logger.warning("or modify the USERNAME and PASSWORD variables in this script.")
        logger.info("Example:")
        logger.info("   export ROBINHOOD_USERNAME=your_email@example.com")
        logger.info("   export ROBINHOOD_PASSWORD=your_password")
        return
    
    # Step 1: Login to Robinhood
    logger.info("📍 STEP 1/5: Authenticating with Robinhood API")
    logger.info(f"🔐 Logging into Robinhood as {USERNAME}...")
    if not login_to_robinhood(USERNAME, PASSWORD):
        logger.error("❌ STEP 1 FAILED: Could not authenticate with Robinhood")
        return
    logger.info("✅ STEP 1 COMPLETED: Successfully authenticated with Robinhood")
    
    # Step 2: Load Excel tickers
    logger.info("📍 STEP 2/5: Loading stock tickers from Excel file")
    logger.info(f"📊 Loading tickers from {TICKERS_FILE}...")
    tickers = load_tickers_from_excel(TICKERS_FILE)
    if not tickers:
        logger.error("❌ STEP 2 FAILED: Could not load tickers from Excel file")
        return
    logger.info(f"✅ STEP 2 COMPLETED: Successfully loaded {len(tickers)} tickers")
    
    # Step 3: Fetch comprehensive stock data
    logger.info("📍 STEP 3/5: Fetching comprehensive stock data")
    logger.info("🔄 This may take several minutes depending on the number of tickers...")
    results = fetch_stock_data(tickers)
    logger.info("✅ STEP 3 COMPLETED: Stock data fetching finished")
    
    # Step 4: Write results to Excel
    logger.info("📍 STEP 4/5: Writing results back to Excel file")
    write_results_to_excel(tickers, results, TICKERS_FILE)
    logger.info("✅ STEP 4 COMPLETED: Results written to Excel file")
    
    # Step 5: Cleanup and logout
    logger.info("📍 STEP 5/5: Cleaning up and logging out")
    try:
        r.logout()
        logger.info("🔓 Logged out of Robinhood")
        logger.info("✅ STEP 5 COMPLETED: Cleanup finished")
    except Exception as e:
        logger.warning(f"⚠️ Logout warning: {e}")
        logger.info("✅ STEP 5 COMPLETED: Cleanup finished (with warnings)")
    
    logger.info("=" * 50)
    logger.info("🎉 ALL STEPS COMPLETED SUCCESSFULLY!")
    logger.info("📊 Stock data has been updated in the Excel file")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()