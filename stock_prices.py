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


def calculate_financial_metrics(stock_data: Dict[str, Any]) -> None:
    """
    Calculate additional financial metrics based on existing data
    
    Args:
        stock_data: Dictionary containing stock data (modified in place)
    """
    try:
        price = stock_data.get('Price')
        high_52w = stock_data.get('52w_High')
        low_52w = stock_data.get('52w_Low')
        pe_ratio = stock_data.get('PE_Ratio')
        recent_support = stock_data.get('Recent_Support')
        recent_resistance = stock_data.get('Recent_Resistance')
        pivot_support_1 = stock_data.get('Pivot_Support_1')
        pivot_resistance_1 = stock_data.get('Pivot_Resistance_1')
        
        # Only calculate if we have valid price data
        if not isinstance(price, (int, float)) or price <= 0:
            return
        
        # 1. Risk/Reward Ratio (based on recent support/resistance)
        if (isinstance(recent_support, (int, float)) and isinstance(recent_resistance, (int, float)) and
            recent_support > 0 and recent_resistance > price):
            risk = price - recent_support
            reward = recent_resistance - price
            if risk > 0:
                stock_data['Risk_Reward_Ratio'] = round(reward / risk, 2)
        
        # 2. Distance from 52-Week High/Low (%)
        if isinstance(high_52w, (int, float)) and high_52w > 0:
            distance_from_high = ((high_52w - price) / high_52w) * 100
            stock_data['Distance_from_52w_High_Pct'] = round(distance_from_high, 2)
        
        if isinstance(low_52w, (int, float)) and low_52w > 0:
            distance_from_low = ((price - low_52w) / low_52w) * 100
            stock_data['Distance_from_52w_Low_Pct'] = round(distance_from_low, 2)
        
        # 3. Upside/Downside Potential (based on pivot levels)
        if isinstance(pivot_resistance_1, (int, float)) and pivot_resistance_1 > price:
            upside_potential = ((pivot_resistance_1 - price) / price) * 100
            stock_data['Upside_Potential_Pct'] = round(upside_potential, 2)
        
        if isinstance(pivot_support_1, (int, float)) and pivot_support_1 > 0 and pivot_support_1 < price:
            downside_risk = ((price - pivot_support_1) / price) * 100
            stock_data['Downside_Risk_Pct'] = round(downside_risk, 2)
        
        # 4. PEG Ratio (would need EPS growth rate - setting to N/A for now as we don't have this data)
        # This would require additional API calls to get earnings growth data
        stock_data['PEG_Ratio'] = 'N/A'
        
        # 5. Valuation Flags
        valuation_flags = []
        entry_flags = []
        price_level_flags = []
        
        # Valuation based on PE ratio
        if isinstance(pe_ratio, (int, float)):
            if pe_ratio < 20:
                valuation_flags.append("Undervalued")
            elif pe_ratio > 30:
                valuation_flags.append("Overvalued")
            else:
                valuation_flags.append("Fair Value")
        
        # Entry opportunity based on risk/reward ratio
        risk_reward = stock_data.get('Risk_Reward_Ratio')
        if isinstance(risk_reward, (int, float)):
            if risk_reward > 2:
                entry_flags.append("Favorable")
            elif risk_reward < 1:
                entry_flags.append("Unfavorable")
            else:
                entry_flags.append("Neutral")
        else:
            entry_flags.append("N/A")
        
        # Price level based on distance from 52w high
        distance_from_high = stock_data.get('Distance_from_52w_High_Pct')
        if isinstance(distance_from_high, (int, float)):
            if distance_from_high < 5:
                price_level_flags.append("Near Top")
            elif distance_from_high > 50:
                price_level_flags.append("Near Bottom")
            else:
                price_level_flags.append("Mid Range")
        
        # Set flag values
        stock_data['Valuation_Flag'] = valuation_flags[0] if valuation_flags else 'N/A'
        stock_data['Entry_Opportunity_Flag'] = entry_flags[0] if entry_flags else 'N/A'
        stock_data['Price_Level_Flag'] = price_level_flags[0] if price_level_flags else 'N/A'
        
        # Calculate AI evaluation matrix logic columns (R-X)
        calculate_ai_evaluation_flags(stock_data)
        
    except Exception as e:
        logger.error(f"Error calculating financial metrics: {e}")
        # Keep default 'N/A' values


def calculate_ai_evaluation_flags(stock_data: Dict[str, Any]) -> None:
    """
    Calculate AI evaluation matrix logic columns (R-X) based on the problem statement formulas
    
    Args:
        stock_data: Dictionary containing stock data (modified in place)
    """
    try:
        current_price = stock_data.get('Price')
        daily_close = stock_data.get('Daily_Close')
        support_level = stock_data.get('Support_Level')  # Traditional support (E)
        resistance_level = stock_data.get('Resistance_Level')  # Traditional resistance (F)
        fib_38_2 = stock_data.get('Fib_38_2')
        fib_50_0 = stock_data.get('Fib_50_0')
        fib_61_8 = stock_data.get('Fib_61_8')
        
        # Only calculate if we have valid price data
        if not isinstance(current_price, (int, float)) or current_price <= 0:
            return
        if not isinstance(daily_close, (int, float)) or daily_close <= 0:
            daily_close = current_price  # Fallback
        
        # Column R: Price Action Flag - TRUE if price is near traditional or Fibonacci levels
        price_action_flag = False
        
        # Check traditional support/resistance levels
        if isinstance(support_level, (int, float)) and support_level > 0:
            if current_price <= support_level * 1.02 and daily_close > support_level:
                price_action_flag = True
        
        if isinstance(resistance_level, (int, float)) and resistance_level > 0:
            if current_price >= resistance_level * 0.99 and daily_close < resistance_level:
                price_action_flag = True
        
        # Check Fibonacci levels
        for fib_level in [fib_38_2, fib_50_0, fib_61_8]:
            if isinstance(fib_level, (int, float)) and fib_level > 0:
                # Check for support bounce near Fibonacci level
                if current_price <= fib_level * 1.02 and daily_close > fib_level:
                    price_action_flag = True
                    break
        
        stock_data['Price_Action_Flag'] = price_action_flag
        
        # Column S: RSI Flag (placeholder - would need RSI calculation)
        # For now, use a simplified version based on support level proximity
        rsi_flag = False
        if isinstance(support_level, (int, float)) and support_level > 0:
            if current_price <= support_level * 1.02:
                rsi_flag = True  # Assume oversold condition near support
        stock_data['RSI_Flag'] = rsi_flag
        
        # Column T: MACD Flag (placeholder - would need MACD calculation)
        # For now, assume positive if price is above recent support
        macd_flag = False
        if isinstance(support_level, (int, float)) and support_level > 0:
            if current_price > support_level:
                macd_flag = True
        stock_data['MACD_Flag'] = macd_flag
        
        # Column U: Volume Flag (placeholder - would need volume data)
        # For now, default to False since we don't have volume data yet
        volume_flag = False
        stock_data['Volume_Flag'] = volume_flag
        
        # Column V: Buy Signal - AND of all flags
        buy_signal = price_action_flag and rsi_flag and macd_flag and volume_flag
        stock_data['Buy_Signal'] = buy_signal
        
        # Column W: Stop-Loss - 2% below lowest of traditional/Fibonacci support
        stop_loss_levels = []
        if isinstance(support_level, (int, float)) and support_level > 0:
            stop_loss_levels.append(support_level)
        if isinstance(fib_38_2, (int, float)) and fib_38_2 > 0:
            stop_loss_levels.append(fib_38_2)
        
        if stop_loss_levels:
            min_support = min(stop_loss_levels)
            stock_data['Stop_Loss'] = round(min_support * 0.98, 2)
        
        # Column X: Target - highest of traditional/Fibonacci resistance
        target_levels = []
        if isinstance(resistance_level, (int, float)) and resistance_level > 0:
            target_levels.append(resistance_level)
        if isinstance(fib_50_0, (int, float)) and fib_50_0 > 0:
            target_levels.append(fib_50_0)
        
        if target_levels:
            max_resistance = max(target_levels)
            stock_data['Target'] = round(max_resistance, 2)
        
    except Exception as e:
        logger.error(f"Error calculating AI evaluation flags: {e}")
        # Keep default values


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
    
    logger.info(f"Fetching stock data for {total_tickers} tickers...")
    
    for i, ticker in enumerate(tickers, 1):
        stock_data = {
            # Basic columns (A-N from problem statement)
            'Date': 'N/A',  # Will be set to current date
            'Ticker': ticker,  # Column B
            'Price': 'N/A',  # Current Price (C)
            'Daily_Close': 'N/A',  # Daily Close (D) - will use same as Price for now
            'Support_Level': 'N/A',  # Traditional support (E) - will use Recent_Support
            'Resistance_Level': 'N/A',  # Traditional resistance (F) - will use Recent_Resistance
            'RSI': 'N/A',  # 14-period RSI (G) - placeholder for now
            'MACD_Line': 'N/A',  # MACD 12,26,9 Line (H) - placeholder for now
            'MACD_Signal': 'N/A',  # MACD Signal Line (I) - placeholder for now
            'MACD_Histogram': 'N/A',  # MACD Histogram (J) - placeholder for now
            'Volume_Current': 'N/A',  # Volume Current Daily (K) - placeholder for now
            'Volume_20_Avg': 'N/A',  # Volume 20-day Average (L) - placeholder for now
            'Trailing_PE': 'N/A',  # Trailing P/E (M) - will use PE_Ratio
            'Forward_PE': 'N/A',  # Forward P/E (N) - placeholder for now
            
            # New Fibonacci columns (O-Q)
            'Swing_High': 'N/A',  # Column O
            'Swing_Low': 'N/A',   # Column P
            'Fib_Support_Resistance': 'N/A',  # Column Q (will contain multiple levels)
            'Fib_38_2': 'N/A',  # Individual Fibonacci levels for calculations
            'Fib_50_0': 'N/A',
            'Fib_61_8': 'N/A',
            
            # Logic columns (R-X) - will be calculated later
            'Price_Action_Flag': False,  # Column R
            'RSI_Flag': False,  # Column S
            'MACD_Flag': False,  # Column T
            'Volume_Flag': False,  # Column U
            'Buy_Signal': False,  # Column V
            'Stop_Loss': 'N/A',  # Column W
            'Target': 'N/A',  # Column X
            
            # Legacy columns to maintain compatibility
            '52w_High': 'N/A', 
            '52w_Low': 'N/A',
            'MarketCap': 'N/A',
            'PE_Ratio': 'N/A',
            'Pivot_Support_1': 'N/A',
            'Pivot_Support_2': 'N/A',
            'Pivot_Resistance_1': 'N/A',
            'Pivot_Resistance_2': 'N/A',
            'Recent_Support': 'N/A',
            'Recent_Resistance': 'N/A',
            'Risk_Reward_Ratio': 'N/A',
            'Distance_from_52w_High_Pct': 'N/A',
            'Distance_from_52w_Low_Pct': 'N/A',
            'Upside_Potential_Pct': 'N/A',
            'Downside_Risk_Pct': 'N/A',
            'PEG_Ratio': 'N/A',
            'Valuation_Flag': 'N/A',
            'Entry_Opportunity_Flag': 'N/A',
            'Price_Level_Flag': 'N/A'
        }
        
        try:
            # Set current date
            stock_data['Date'] = datetime.now().strftime('%Y-%m-%d')
            
            # Get current price from quotes
            quote_data = r.stocks.get_quotes(ticker)
            if quote_data and isinstance(quote_data, list) and len(quote_data) > 0:
                quote_item = quote_data[0]
                if isinstance(quote_item, dict):
                    price = quote_item.get('last_trade_price')
                    if price:
                        current_price = float(price)
                        stock_data['Price'] = current_price
                        stock_data['Daily_Close'] = current_price  # Use same value for now
                else:
                    logger.warning(f"{i}/{total_tickers} {ticker}: Quote data item is not a dict, got {type(quote_item)}")
            elif quote_data is None:
                logger.warning(f"{i}/{total_tickers} {ticker}: No quote data returned (likely invalid ticker)")
            elif isinstance(quote_data, list) and len(quote_data) == 0:
                logger.warning(f"{i}/{total_tickers} {ticker}: Empty quote data list returned (likely invalid ticker)")
            else:
                logger.warning(f"{i}/{total_tickers} {ticker}: Unexpected quote data format: {type(quote_data)}")
            
            # Get fundamentals data
            fundamental_data = r.stocks.get_fundamentals(ticker)
            if fundamental_data and isinstance(fundamental_data, list) and len(fundamental_data) > 0:
                fund = fundamental_data[0]
                if isinstance(fund, dict):
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
                else:
                    logger.warning(f"{i}/{total_tickers} {ticker}: Fundamental data item is not a dict, got {type(fund)}")
            elif fundamental_data is None:
                logger.warning(f"{i}/{total_tickers} {ticker}: No fundamental data returned (likely invalid ticker)")
            elif isinstance(fundamental_data, list) and len(fundamental_data) == 0:
                logger.warning(f"{i}/{total_tickers} {ticker}: Empty fundamental data list returned (likely invalid ticker)")
            else:
                logger.warning(f"{i}/{total_tickers} {ticker}: Unexpected fundamental data format: {type(fundamental_data)}")
            
            # Calculate technical levels (Support & Resistance)
            logger.debug(f"{i}/{total_tickers} {ticker}: Calculating technical levels...")
            technical_levels = calculate_technical_levels(ticker)
            
            # Add technical analysis results with defensive checks
            if technical_levels and isinstance(technical_levels, dict):
                # Legacy technical data
                stock_data.update({
                    'Pivot_Support_1': technical_levels.get('pivot_support_1', 'N/A'),
                    'Pivot_Support_2': technical_levels.get('pivot_support_2', 'N/A'),
                    'Pivot_Resistance_1': technical_levels.get('pivot_resistance_1', 'N/A'),
                    'Pivot_Resistance_2': technical_levels.get('pivot_resistance_2', 'N/A'),
                    'Recent_Support': technical_levels.get('recent_support', 'N/A'),
                    'Recent_Resistance': technical_levels.get('recent_resistance', 'N/A')
                })
                
                # New AI evaluation matrix columns
                # Map Recent_Support/Resistance to traditional Support/Resistance columns
                stock_data['Support_Level'] = technical_levels.get('recent_support', 'N/A')
                stock_data['Resistance_Level'] = technical_levels.get('recent_resistance', 'N/A')
                stock_data['Trailing_PE'] = stock_data.get('PE_Ratio', 'N/A')
                
                # New Fibonacci columns
                stock_data['Swing_High'] = technical_levels.get('swing_high', 'N/A')
                stock_data['Swing_Low'] = technical_levels.get('swing_low', 'N/A')
                stock_data['Fib_38_2'] = technical_levels.get('fib_38_2', 'N/A')
                stock_data['Fib_50_0'] = technical_levels.get('fib_50_0', 'N/A')
                stock_data['Fib_61_8'] = technical_levels.get('fib_61_8', 'N/A')
                
                # Create combined Fibonacci support/resistance text
                fib_levels = []
                for level, pct in [('fib_38_2', '38.2%'), ('fib_50_0', '50%'), ('fib_61_8', '61.8%')]:
                    value = technical_levels.get(level)
                    if isinstance(value, (int, float)):
                        fib_levels.append(f"{pct}: ${value:.2f}")
                stock_data['Fib_Support_Resistance'] = ' | '.join(fib_levels) if fib_levels else 'N/A'
            else:
                logger.warning(f"{i}/{total_tickers} {ticker}: Technical levels calculation returned invalid data: {type(technical_levels)}")
                # Keep default 'N/A' values already set in stock_data
            
            # Calculate additional financial metrics
            logger.debug(f"{i}/{total_tickers} {ticker}: Calculating financial metrics...")
            calculate_financial_metrics(stock_data)
            
            results[ticker] = stock_data
            logger.info(f"{i}/{total_tickers} {ticker}: ${stock_data['Price']} | "
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
                'Recent_Resistance': 'N/A',
                'Risk_Reward_Ratio': 'N/A',
                'Distance_from_52w_High_Pct': 'N/A',
                'Distance_from_52w_Low_Pct': 'N/A',
                'Upside_Potential_Pct': 'N/A',
                'Downside_Risk_Pct': 'N/A',
                'PEG_Ratio': 'N/A',
                'Valuation_Flag': 'N/A',
                'Entry_Opportunity_Flag': 'N/A',
                'Price_Level_Flag': 'N/A'
            }
            logger.warning(f"{i}/{total_tickers} {ticker}: {error_msg}")
    
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
                # AI Evaluation Matrix columns (A-X) in correct order
                'Date': stock_data.get('Date', 'N/A'),  # A
                'Ticker': ticker,  # B (Stock Ticker)
                'Current_Price': stock_data.get('Price', 'N/A'),  # C
                'Daily_Close': stock_data.get('Daily_Close', 'N/A'),  # D
                'Support_Level': stock_data.get('Support_Level', 'N/A'),  # E
                'Resistance_Level': stock_data.get('Resistance_Level', 'N/A'),  # F
                'RSI': stock_data.get('RSI', 'N/A'),  # G
                'MACD_Line': stock_data.get('MACD_Line', 'N/A'),  # H
                'MACD_Signal': stock_data.get('MACD_Signal', 'N/A'),  # I
                'MACD_Histogram': stock_data.get('MACD_Histogram', 'N/A'),  # J
                'Volume_Current': stock_data.get('Volume_Current', 'N/A'),  # K
                'Volume_20_Avg': stock_data.get('Volume_20_Avg', 'N/A'),  # L
                'Trailing_PE': stock_data.get('Trailing_PE', 'N/A'),  # M
                'Forward_PE': stock_data.get('Forward_PE', 'N/A'),  # N
                'Swing_High': stock_data.get('Swing_High', 'N/A'),  # O
                'Swing_Low': stock_data.get('Swing_Low', 'N/A'),  # P
                'Fibonacci_Levels': stock_data.get('Fib_Support_Resistance', 'N/A'),  # Q
                'Price_Action_Flag': stock_data.get('Price_Action_Flag', False),  # R
                'RSI_Flag': stock_data.get('RSI_Flag', False),  # S
                'MACD_Flag': stock_data.get('MACD_Flag', False),  # T
                'Volume_Flag': stock_data.get('Volume_Flag', False),  # U
                'Buy_Signal': stock_data.get('Buy_Signal', False),  # V
                'Stop_Loss': stock_data.get('Stop_Loss', 'N/A'),  # W
                'Target': stock_data.get('Target', 'N/A'),  # X
                
                # Legacy columns for backward compatibility
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
                'Recent_Resistance': stock_data.get('Recent_Resistance', 'N/A'),
                'Risk_Reward_Ratio': stock_data.get('Risk_Reward_Ratio', 'N/A'),
                'Distance_from_52w_High_Pct': stock_data.get('Distance_from_52w_High_Pct', 'N/A'),
                'Distance_from_52w_Low_Pct': stock_data.get('Distance_from_52w_Low_Pct', 'N/A'),
                'Upside_Potential_Pct': stock_data.get('Upside_Potential_Pct', 'N/A'),
                'Downside_Risk_Pct': stock_data.get('Downside_Risk_Pct', 'N/A'),
                'PEG_Ratio': stock_data.get('PEG_Ratio', 'N/A'),
                'Valuation_Flag': stock_data.get('Valuation_Flag', 'N/A'),
                'Entry_Opportunity_Flag': stock_data.get('Entry_Opportunity_Flag', 'N/A'),
                'Price_Level_Flag': stock_data.get('Price_Level_Flag', 'N/A')
            }
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Write to Excel using openpyxl engine
        df.to_excel(file_path, engine='openpyxl', index=False)
        
        logger.info(f"Results written to {file_path}")
        
        # Log summary for user
        logger.info("STOCK DATA SUMMARY")
        logger.info("=" * 70)
        
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
            risk_reward = row['Risk_Reward_Ratio']
            dist_high = row['Distance_from_52w_High_Pct']
            dist_low = row['Distance_from_52w_Low_Pct']
            valuation = row['Valuation_Flag']
            entry_opp = row['Entry_Opportunity_Flag']
            price_level = row['Price_Level_Flag']
            
            if isinstance(price, (int, float)):
                logger.info(f"{ticker:>8}: ${safe_format_price(price)} | "
                           f"52w: ${safe_format_number(high_52w, '>8.2f')}-${safe_format_number(low_52w, '>8.2f')} | "
                           f"Cap: {safe_format_number(market_cap, '>12.0f')} | "
                           f"P/E: {safe_format_number(pe_ratio, '>6.2f')}")
                logger.info(f"{'':>8}  Pivot S/R: {safe_format_number(pivot_sup1, '.2f')}-{safe_format_number(pivot_res1, '.2f')} | "
                           f"Recent S/R: {safe_format_number(recent_sup, '.2f')}-{safe_format_number(recent_res, '.2f')} | "
                           f"R/R: {safe_format_number(risk_reward, '.2f')}")
                logger.info(f"{'':>8}  52w Dist: H{safe_format_number(dist_high, '.1f')}% L{safe_format_number(dist_low, '.1f')}% | "
                           f"Val: {valuation} | Entry: {entry_opp} | Level: {price_level}")
            else:
                logger.info(f"{ticker:>8}: {str(price):>12} | Data: N/A")
        
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Error writing results to Excel: {e}")
        # Fall back to logging results
        logger.info("STOCK DATA (Excel write failed)")
        logger.info("=" * 50)
        for ticker, data in results.items():
            logger.info(f"{ticker}: {data}")
        logger.info("=" * 50)


def main():
    """Main function to orchestrate the stock price fetching process"""
    logger.info("🚀 Stock Data Fetcher - Robinhood Edition")
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
    logger.info(f"🔐 Logging into Robinhood as {USERNAME}...")
    if not login_to_robinhood(USERNAME, PASSWORD):
        return
    
    # Step 2: Load Excel tickers
    logger.info(f"📊 Loading tickers from {TICKERS_FILE}...")
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
        logger.info("Logged out of Robinhood")
    except Exception as e:
        logger.warning(f"Logout warning: {e}")


if __name__ == "__main__":
    main()