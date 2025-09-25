#!/usr/bin/env python3
"""
Stock Data Fetcher using Twelve Data API

This script fetches comprehensive stock data for tickers listed in an Excel file
using the Twelve Data API. It retrieves current price, 52-week high/low, 
market capitalization, and other stock data, then writes the results
back to the Excel file.
"""

import requests
import pandas as pd
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from technical_analysis import calculate_technical_levels
from logging_config import get_logger

# Get logger instance
logger = get_logger('stocks_app.stock_prices')

# Configuration variables - can be set via environment variables or modified here
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY") or os.getenv("api_key", "your_twelvedata_api_key")
TICKERS_FILE = os.getenv("TICKERS_FILE", "tickers.xlsx")


def get_stock_data_from_api(ticker: str) -> Dict[str, Any]:
    """
    Fetch stock data from Twelve Data API.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary containing stock data
    """
    if TWELVEDATA_API_KEY in ["your_twelvedata_api_key", None, ""]:
        logger.warning(f"No API key configured, using mock data for {ticker}")
        return get_mock_stock_data(ticker)
    
    try:
        # Get current price
        price_url = "https://api.twelvedata.com/price" 
        price_params = {
            'symbol': ticker,
            'apikey': TWELVEDATA_API_KEY
        }
        
        price_response = requests.get(price_url, params=price_params, timeout=30)
        current_price = None
        
        if price_response.status_code == 200:
            price_data = price_response.json()
            if 'price' in price_data:
                current_price = float(price_data['price'])
        
        # Get quote data for additional information
        quote_url = "https://api.twelvedata.com/quote"
        quote_params = {
            'symbol': ticker,
            'apikey': TWELVEDATA_API_KEY
        }
        
        quote_response = requests.get(quote_url, params=quote_params, timeout=30)
        quote_data = {}
        
        if quote_response.status_code == 200:
            quote_data = quote_response.json()
        
        # Extract data from API response
        stock_data = {
            'Ticker': ticker,
            'Current_Price': current_price or quote_data.get('close', 'N/A'),
            'Previous_Close': quote_data.get('previous_close', 'N/A'),
            'Open': quote_data.get('open', 'N/A'),
            'High': quote_data.get('high', 'N/A'),
            'Low': quote_data.get('low', 'N/A'),
            'Volume': quote_data.get('volume', 'N/A'),
            '52_Week_High': quote_data.get('fifty_two_week_high', 'N/A'),
            '52_Week_Low': quote_data.get('fifty_two_week_low', 'N/A'),
            'Market_Cap': quote_data.get('market_cap', 'N/A'),
            'PE_Ratio': quote_data.get('pe_ratio', 'N/A'),
            'data_source': 'Twelve Data API',
            'last_updated': datetime.now().isoformat()
        }
        
        # Calculate additional metrics if we have price data
        if current_price and isinstance(current_price, (int, float)):
            try:
                # Calculate technical levels using the existing function
                technical_levels = calculate_technical_levels(current_price)
                stock_data.update(technical_levels)
            except Exception as e:
                logger.warning(f"Could not calculate technical levels for {ticker}: {e}")
        
        logger.info(f"✅ Successfully fetched data for {ticker}: ${current_price}")
        return stock_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {ticker}: {e}")
        return get_mock_stock_data(ticker)
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        return get_mock_stock_data(ticker)


def get_mock_stock_data(ticker: str) -> Dict[str, Any]:
    """
    Generate mock stock data for testing when API is unavailable.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary containing mock stock data
    """
    import hashlib
    import random
    
    # Generate deterministic "random" values based on ticker hash
    seed = int(hashlib.md5(ticker.encode()).hexdigest()[:8], 16)
    random.seed(seed)
    
    # Mock current price (between $10-$500)
    current_price = round(random.uniform(10, 500), 2)
    previous_close = round(current_price * random.uniform(0.95, 1.05), 2)
    
    stock_data = {
        'Ticker': ticker,
        'Current_Price': current_price,
        'Previous_Close': previous_close,
        'Open': round(current_price * random.uniform(0.98, 1.02), 2),
        'High': round(current_price * random.uniform(1.01, 1.08), 2),
        'Low': round(current_price * random.uniform(0.92, 0.99), 2),
        'Volume': int(random.uniform(100000, 10000000)),
        '52_Week_High': round(current_price * random.uniform(1.2, 2.0), 2),
        '52_Week_Low': round(current_price * random.uniform(0.5, 0.8), 2),
        'Market_Cap': f"{random.randint(1, 500)}B",
        'PE_Ratio': round(random.uniform(10, 35), 2),
        'data_source': 'Mock Data',
        'last_updated': datetime.now().isoformat()
    }
    
    # Calculate technical levels
    try:
        technical_levels = calculate_technical_levels(current_price)
        stock_data.update(technical_levels)
    except Exception as e:
        logger.warning(f"Could not calculate technical levels for {ticker}: {e}")
    
    return stock_data



def load_tickers_from_excel(filename: str) -> List[str]:
    """
    Load stock tickers from Excel file.
    
    Args:
        filename: Path to Excel file containing ticker symbols
        
    Returns:
        List of ticker symbols
    """
    try:
        # Load the Excel file
        df = pd.read_excel(filename)
        
        # Look for ticker column (case insensitive)
        ticker_column = None
        for column in df.columns:
            if column.lower() in ['ticker', 'symbol', 'stock', 'tickers']:
                ticker_column = column
                break
        
        if ticker_column is None:
            logger.error(f"No ticker column found in {filename}")
            logger.error(f"Available columns: {list(df.columns)}")
            return []
        
        # Extract unique tickers and remove any NaN/empty values
        tickers = df[ticker_column].dropna().astype(str).str.upper().unique().tolist()
        logger.info(f"Loaded {len(tickers)} unique tickers from {filename}")
        return tickers
        
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return []
    except Exception as e:
        logger.error(f"Error loading tickers from {filename}: {e}")
        return []


def fetch_stock_data(tickers: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch stock data for multiple tickers using Twelve Data API.
    
    Args:
        tickers: List of stock ticker symbols
        
    Returns:
        List of dictionaries containing stock data
    """
    results = []
    total = len(tickers)
    
    logger.info(f"Fetching data for {total} tickers...")
    
    for i, ticker in enumerate(tickers, 1):
        logger.info(f"Processing {ticker} ({i}/{total})")
        
        try:
            stock_data = get_stock_data_from_api(ticker)
            results.append(stock_data)
            
            # Progress updates
            if i % 10 == 0:
                logger.info(f"✅ Progress: {i}/{total} tickers processed")
                
            # Rate limiting - small delay between requests
            if i < total:  # Don't delay after the last request
                import time
                time.sleep(1)  # 1 second delay between requests
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch data for {ticker}: {e}")
            # Add a minimal entry to avoid breaking the process
            results.append({
                'Ticker': ticker,
                'Current_Price': 'Error',
                'data_source': 'Error',
                'last_updated': datetime.now().isoformat(),
                'error': str(e)
            })
    
    logger.info(f"✅ Completed fetching data for {len(results)} tickers")
    return results


def save_results_to_excel(results: List[Dict[str, Any]], filename: str) -> bool:
    """
    Save stock data results to Excel file.
    
    Args:
        results: List of stock data dictionaries
        filename: Output Excel filename
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Create backup if file already exists
        if os.path.exists(filename):
            backup_filename = f"{filename.replace('.xlsx', '')}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            import shutil
            shutil.copy2(filename, backup_filename)
            logger.info(f"Created backup: {backup_filename}")
        
        # Save to Excel
        df.to_excel(filename, index=False)
        logger.info(f"✅ Successfully saved {len(results)} records to {filename}")
        
        # Log summary statistics
        successful_fetches = len([r for r in results if r.get('data_source') != 'Error'])
        logger.info(f"📊 Summary: {successful_fetches}/{len(results)} successful data fetches")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving results to {filename}: {e}")
        return False
def main():
    """Main function to orchestrate the stock price fetching process"""
    logger.info("🚀 Stock Data Fetcher - Twelve Data API Edition")
    logger.info("=" * 50)
    logger.info("📋 STARTING MAIN EXECUTION STEPS")
    logger.info("=" * 50)
    
    # Check if API key is set
    if TWELVEDATA_API_KEY in ["your_twelvedata_api_key", None, ""]:
        logger.warning("⚠️ No Twelve Data API key configured!")
        logger.warning("Set TWELVEDATA_API_KEY environment variable with your API key")
        logger.warning("Get your free API key from: https://twelvedata.com/")
        logger.info("Example:")
        logger.info("   export TWELVEDATA_API_KEY=your_api_key_here")
        logger.warning("Proceeding with mock data for testing...")
    
    # Step 1: Load Excel tickers
    logger.info("📍 STEP 1/4: Loading stock tickers from Excel file")
    logger.info(f"📊 Loading tickers from {TICKERS_FILE}...")
    tickers = load_tickers_from_excel(TICKERS_FILE)
    if not tickers:
        logger.error("❌ STEP 1 FAILED: Could not load tickers from Excel file")
        return
    logger.info(f"✅ STEP 1 COMPLETED: Successfully loaded {len(tickers)} tickers")
    
    # Step 2: Fetch stock data
    logger.info("📍 STEP 2/4: Fetching stock data from Twelve Data API")
    logger.info("🔄 This may take several minutes depending on the number of tickers...")
    results = fetch_stock_data(tickers)
    logger.info("✅ STEP 2 COMPLETED: Stock data fetching finished")
    
    # Step 3: Write results to Excel
    logger.info("📍 STEP 3/4: Writing results back to Excel file")
    success = save_results_to_excel(results, TICKERS_FILE)
    if success:
        logger.info("✅ STEP 3 COMPLETED: Results written to Excel file")
    else:
        logger.error("❌ STEP 3 FAILED: Could not write results to Excel file")
        return
    
    # Step 4: Summary
    logger.info("📍 STEP 4/4: Summary and cleanup")
    logger.info("=" * 50)
    logger.info("🎉 ALL STEPS COMPLETED SUCCESSFULLY!")
    logger.info("📊 Stock data has been updated in the Excel file")
    if TWELVEDATA_API_KEY in ["your_twelvedata_api_key", None, ""]:
        logger.info("💡 Note: Mock data was used. Configure API key for real data.")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()