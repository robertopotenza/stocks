#!/usr/bin/env python3
"""
Technical Analysis Module for Support and Resistance Levels

This module provides functions to calculate technical support and resistance levels
from historical stock price data using various algorithms including pivot points,
recent highs/lows, and volume-weighted analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import robin_stocks.robinhood as r
from logging_config import get_logger

# Get logger instance
logger = get_logger('stocks_app.technical_analysis')


def get_historical_data(ticker: str, interval: str = 'day', span: str = '3month') -> List[Dict[str, Any]]:
    """
    Fetch historical stock data for technical analysis
    
    Args:
        ticker: Stock ticker symbol
        interval: Data interval ('5minute', '10minute', 'hour', 'day', 'week')
        span: Time span ('day', 'week', 'month', '3month', 'year', '5year')
        
    Returns:
        List of historical data dictionaries with OHLCV data
    """
    try:
        historical_data = r.stocks.get_stock_historicals(
            inputSymbols=ticker,
            interval=interval,
            span=span,
            bounds='regular'
        )
        
        if not historical_data:
            return []
            
        # Filter out None values and convert price strings to floats
        clean_data = []
        for data_point in historical_data:
            if not isinstance(data_point, dict):
                continue

            if all(data_point.get(key) is not None for key in ['open_price', 'high_price', 'low_price', 'close_price']):
                try:
                    clean_point = {
                        'date': data_point['begins_at'],
                        'open': float(data_point['open_price']),
                        'high': float(data_point['high_price']),
                        'low': float(data_point['low_price']),
                        'close': float(data_point['close_price']),
                        'volume': int(data_point.get('volume', 0)) if data_point.get('volume') else 0
                    }
                    clean_data.append(clean_point)
                except (ValueError, TypeError):
                    continue
                    
        # Sort the clean data by date to ensure consistent ordering (most recent last)
        clean_data.sort(key=lambda x: x['date'])
        
        return clean_data
        
    except Exception as e:
        logger.error(f"Error fetching historical data for {ticker}: {e}")
        return []


def calculate_pivot_points(data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate pivot points based support and resistance levels
    
    Pivot Point = (High + Low + Close) / 3
    Support 1 = (2 * PP) - High
    Support 2 = PP - (High - Low)  
    Resistance 1 = (2 * PP) - Low
    Resistance 2 = PP + (High - Low)
    
    Args:
        data: List of OHLCV data dictionaries
        
    Returns:
        Dictionary with pivot point levels
    """
    if not data or len(data) < 2:
        return {}
        
    try:
        # Use the most recent complete trading day
        recent = data[-1]
        high = recent['high']
        low = recent['low'] 
        close = recent['close']
        
        # Calculate pivot point
        pivot_point = (high + low + close) / 3
        
        # Calculate support and resistance levels
        support_1 = (2 * pivot_point) - high
        support_2 = pivot_point - (high - low)
        resistance_1 = (2 * pivot_point) - low
        resistance_2 = pivot_point + (high - low)
        
        return {
            'pivot_point': round(pivot_point, 2),
            'support_1': round(support_1, 2),
            'support_2': round(support_2, 2),
            'resistance_1': round(resistance_1, 2),
            'resistance_2': round(resistance_2, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating pivot points: {e}")
        return {}


def find_recent_support_resistance(data: List[Dict[str, Any]], lookback_days: int = 20) -> Dict[str, float]:
    """
    Find support and resistance levels based on recent highs and lows
    
    Args:
        data: List of OHLCV data dictionaries
        lookback_days: Number of recent days to analyze
        
    Returns:
        Dictionary with recent support and resistance levels
    """
    if not data or len(data) < lookback_days:
        return {}
        
    try:
        # Get recent data
        recent_data = data[-lookback_days:] if len(data) >= lookback_days else data
        
        # Extract highs and lows
        highs = [d['high'] for d in recent_data]
        lows = [d['low'] for d in recent_data]
        
        # Find significant levels using local maxima/minima
        resistance_levels = []
        support_levels = []
        
        # Simple approach: find the highest high and lowest low in the period
        # Also find secondary levels
        sorted_highs = sorted(set(highs), reverse=True)
        sorted_lows = sorted(set(lows))
        
        # Take top resistance levels
        if len(sorted_highs) >= 1:
            resistance_levels.append(sorted_highs[0])
        if len(sorted_highs) >= 2:
            resistance_levels.append(sorted_highs[1])
            
        # Take bottom support levels  
        if len(sorted_lows) >= 1:
            support_levels.append(sorted_lows[0])
        if len(sorted_lows) >= 2:
            support_levels.append(sorted_lows[1])
            
        result = {}
        if resistance_levels:
            result['recent_resistance_1'] = round(resistance_levels[0], 2)
            if len(resistance_levels) > 1:
                result['recent_resistance_2'] = round(resistance_levels[1], 2)
                
        if support_levels:
            result['recent_support_1'] = round(support_levels[0], 2)
            if len(support_levels) > 1:
                result['recent_support_2'] = round(support_levels[1], 2)
                
        return result
        
    except Exception as e:
        logger.error(f"Error finding recent support/resistance: {e}")
        return {}


def calculate_fibonacci_levels(high: float, low: float) -> Dict[str, float]:
    """
    Calculate Fibonacci retracement levels from swing high and low
    
    Args:
        high: Swing high price
        low: Swing low price
        
    Returns:
        Dictionary containing Fibonacci levels (23.6%, 38.2%, 50%, 61.8%)
    """
    try:
        if not isinstance(high, (int, float)) or not isinstance(low, (int, float)) or high <= low:
            return {}
        
        # Calculate the range
        price_range = high - low
        
        # Calculate Fibonacci levels (for downtrend, these act as support)
        fibonacci_levels = {
            'fib_23_6': round(high - (price_range * 0.236), 2),
            'fib_38_2': round(high - (price_range * 0.382), 2),
            'fib_50_0': round(high - (price_range * 0.500), 2),
            'fib_61_8': round(high - (price_range * 0.618), 2)
        }
        
        return fibonacci_levels
        
    except Exception as e:
        logger.error(f"Error calculating Fibonacci levels: {e}")
        return {}


def find_swing_high_low(data: List[Dict[str, Any]], lookback_days: int = 60) -> Dict[str, float]:
    """
    Find swing high and low from historical data
    
    Args:
        data: List of historical price data dictionaries
        lookback_days: Number of days to look back for swing points
        
    Returns:
        Dictionary containing swing_high and swing_low
    """
    try:
        if not data or len(data) < 5:
            return {}
        
        # Sort data by date to ensure proper chronology
        sorted_data = sorted(data, key=lambda x: x['date'])
        
        # Use the specified lookback period or all available data if less
        recent_data = sorted_data[-min(lookback_days, len(sorted_data)):]
        
        # Find swing high and low
        highs = [float(d['high']) for d in recent_data if isinstance(d.get('high'), (int, float, str))]
        lows = [float(d['low']) for d in recent_data if isinstance(d.get('low'), (int, float, str))]
        
        if not highs or not lows:
            return {}
        
        swing_high = max(highs)
        swing_low = min(lows)
        
        return {
            'swing_high': round(swing_high, 2),
            'swing_low': round(swing_low, 2)
        }
        
    except Exception as e:
        logger.error(f"Error finding swing high/low: {e}")
        return {}


def calculate_technical_levels(ticker: str) -> Dict[str, Any]:
    """
    Calculate comprehensive technical support and resistance levels for a ticker
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary containing various technical levels and analysis
    """
    try:
        # Get historical data (3 months of daily data)
        historical_data = get_historical_data(ticker, interval='day', span='3month')
        
        if not historical_data or len(historical_data) < 5:
            logger.warning(f"Insufficient historical data for {ticker}: {len(historical_data) if historical_data else 0} data points")
            return {
                'pivot_support_1': 'N/A',
                'pivot_support_2': 'N/A', 
                'pivot_resistance_1': 'N/A',
                'pivot_resistance_2': 'N/A',
                'recent_support': 'N/A',
                'recent_resistance': 'N/A',
                'swing_high': 'N/A',
                'swing_low': 'N/A',
                'fib_38_2': 'N/A',
                'fib_50_0': 'N/A',
                'fib_61_8': 'N/A',
                'error': 'Insufficient historical data'
            }
        
        # Calculate pivot points
        pivot_levels = calculate_pivot_points(historical_data)
        
        # Calculate recent support/resistance
        recent_levels = find_recent_support_resistance(historical_data, lookback_days=20)
        
        # Calculate swing high/low and Fibonacci levels
        swing_levels = find_swing_high_low(historical_data, lookback_days=60)
        fibonacci_levels = {}
        
        if swing_levels and 'swing_high' in swing_levels and 'swing_low' in swing_levels:
            fibonacci_levels = calculate_fibonacci_levels(
                swing_levels['swing_high'], 
                swing_levels['swing_low']
            )
        
        # Combine results with defensive checks
        result = {
            'pivot_support_1': pivot_levels.get('support_1', 'N/A') if isinstance(pivot_levels, dict) else 'N/A',
            'pivot_support_2': pivot_levels.get('support_2', 'N/A') if isinstance(pivot_levels, dict) else 'N/A',
            'pivot_resistance_1': pivot_levels.get('resistance_1', 'N/A') if isinstance(pivot_levels, dict) else 'N/A',
            'pivot_resistance_2': pivot_levels.get('resistance_2', 'N/A') if isinstance(pivot_levels, dict) else 'N/A',
            'recent_support': recent_levels.get('recent_support_1', 'N/A') if isinstance(recent_levels, dict) else 'N/A',
            'recent_resistance': recent_levels.get('recent_resistance_1', 'N/A') if isinstance(recent_levels, dict) else 'N/A',
            'swing_high': swing_levels.get('swing_high', 'N/A') if isinstance(swing_levels, dict) else 'N/A',
            'swing_low': swing_levels.get('swing_low', 'N/A') if isinstance(swing_levels, dict) else 'N/A',
            'fib_23_6': fibonacci_levels.get('fib_23_6', 'N/A') if isinstance(fibonacci_levels, dict) else 'N/A',
            'fib_38_2': fibonacci_levels.get('fib_38_2', 'N/A') if isinstance(fibonacci_levels, dict) else 'N/A',
            'fib_50_0': fibonacci_levels.get('fib_50_0', 'N/A') if isinstance(fibonacci_levels, dict) else 'N/A',
            'fib_61_8': fibonacci_levels.get('fib_61_8', 'N/A') if isinstance(fibonacci_levels, dict) else 'N/A',
            'data_points': len(historical_data)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating technical levels for {ticker}: {e}")
        return {
            'pivot_support_1': 'N/A',
            'pivot_support_2': 'N/A',
            'pivot_resistance_1': 'N/A', 
            'pivot_resistance_2': 'N/A',
            'recent_support': 'N/A',
            'recent_resistance': 'N/A',
            'swing_high': 'N/A',
            'swing_low': 'N/A',
            'fib_23_6': 'N/A',
            'fib_38_2': 'N/A',
            'fib_50_0': 'N/A',
            'fib_61_8': 'N/A',
            'error': str(e)
        }