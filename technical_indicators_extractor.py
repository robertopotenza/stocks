#!/usr/bin/env python3
"""
Technical Indicators Extractor Module - Twelve Data API Edition

This module extracts technical indicators using the Twelve Data API.
It supports extraction of:
- Woodie's Pivot Points (Pivot, S1, S2, R1, R2)
- Moving Averages: EMA20, SMA50
- RSI (14)
- MACD (value/histogram/signal)
- Bollinger Bands (upper, middle, lower)
- Volume (daily)
- ADX(14)
- ATR(14)

Uses reliable API-based data instead of web scraping for better performance
and reliability.
"""

import pandas as pd
import os
import sys
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import argparse
from logging_config import get_logger

# Get logger instance
logger = get_logger('stocks_app.technical_indicators')

class TechnicalIndicatorsExtractor:
    """
    Main class for extracting technical indicators using Twelve Data API.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        delay_min: float = 1.0,
        delay_max: float = 2.0,
        # Keep these parameters for backward compatibility
        headless: bool = True,
        timeout: int = 30
    ):
        """
        Initialize the Technical Indicators Extractor.
        
        Args:
            api_key: Twelve Data API key (if None, will try environment variable)
            delay_min: Minimum delay between API requests in seconds
            delay_max: Maximum delay between API requests in seconds
            headless: Kept for backward compatibility (not used)
            timeout: Kept for backward compatibility (not used)
        """
        self.api_key = api_key or os.getenv('TWELVEDATA_API_KEY') or os.getenv('api_key')
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.base_url = "https://api.twelvedata.com"
        
        if not self.api_key or self.api_key == "your_twelvedata_api_key":
            logger.warning("No Twelve Data API key provided. Using mock data.")
            self.use_mock_data = True
        else:
            self.use_mock_data = False
            logger.info("Twelve Data API key configured successfully")
    
    def _random_delay(self):
        """Add random delay between requests to avoid rate limiting."""
        import random
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
    
    def _make_api_request(self, endpoint: str, params: Dict[str, str]) -> Optional[Dict]:
        """
        Make a request to the Twelve Data API.
        
        Args:
            endpoint: API endpoint (e.g., 'rsi', 'macd', etc.)
            params: Request parameters
            
        Returns:
            JSON response or None if failed
        """
        if self.use_mock_data:
            return None
            
        # Add API key to parameters
        params['apikey'] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API error responses
            if 'status' in data and data['status'] == 'error':
                logger.warning(f"API error for {endpoint}: {data.get('message', 'Unknown error')}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"API request failed for {endpoint}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error for {endpoint}: {e}")
            return None
    
    def _get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price for a ticker using Twelve Data API."""
        params = {
            'symbol': ticker,
            'interval': '1day',
            'outputsize': '1'
        }
        
        data = self._make_api_request('price', params)
        if data and 'price' in data:
            try:
                return float(data['price'])
            except (ValueError, TypeError):
                pass
        return None
    
    def _calculate_pivot_points(self, high: float, low: float, close: float) -> Dict[str, float]:
        """Calculate Woodie's Pivot Points."""
        pivot = (high + low + 2 * close) / 4
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        
        return {
            'Woodies_Pivot': round(pivot, 2),
            'Woodies_S1': round(s1, 2),
            'Woodies_S2': round(s2, 2),
            'Woodies_R1': round(r1, 2),
            'Woodies_R2': round(r2, 2)
        }
    
    def _get_historical_data(self, ticker: str, days: int = 50) -> Optional[Dict]:
        """Get historical price data for calculations."""
        params = {
            'symbol': ticker,
            'interval': '1day',
            'outputsize': str(days)
        }
        
        return self._make_api_request('time_series', params)
    
    def _extract_technical_indicator(self, ticker: str, indicator: str, **kwargs) -> Optional[float]:
        """Extract a single technical indicator."""
        params = {
            'symbol': ticker,
            'interval': '1day',
            **kwargs
        }
        
        data = self._make_api_request(indicator, params)
        if data and 'values' in data and len(data['values']) > 0:
            latest_value = data['values'][0]
            if isinstance(latest_value, dict):
                # Find the indicator value (usually the second field after datetime)
                for key, value in latest_value.items():
                    if key != 'datetime':
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            continue
        return None
    
    def _generate_mock_indicators(self, ticker: str) -> Dict[str, Any]:
        """Generate consistent mock data for testing when API is unavailable."""
        import hashlib
        
        # Generate deterministic "random" values based on ticker hash
        seed = int(hashlib.md5(ticker.encode()).hexdigest()[:8], 16)
        import random
        random.seed(seed)
        
        # Mock current price (between $10-$500)
        price = round(random.uniform(10, 500), 2)
        
        # Mock pivot points based on price
        high = price * random.uniform(1.02, 1.05)
        low = price * random.uniform(0.95, 0.98)
        pivot_data = self._calculate_pivot_points(high, low, price)
        
        mock_indicators = {
            **pivot_data,
            'EMA20': round(price * random.uniform(0.98, 1.02), 2),
            'SMA50': round(price * random.uniform(0.95, 1.05), 2),
            'RSI_14': round(random.uniform(20, 80), 2),
            'MACD_value': round(random.uniform(-2, 2), 4),
            'MACD_signal': round(random.uniform(-2, 2), 4),
            'MACD_histogram': round(random.uniform(-1, 1), 4),
            'Bollinger_upper': round(price * random.uniform(1.05, 1.15), 2),
            'Bollinger_middle': round(price, 2),
            'Bollinger_lower': round(price * random.uniform(0.85, 0.95), 2),
            'Volume_daily': int(random.uniform(100000, 10000000)),
            'ADX_14': round(random.uniform(10, 60), 2),
            'ATR_14': round(random.uniform(0.5, 5.0), 4)
        }
        
        return mock_indicators
    
    def extract_indicators_for_ticker(self, ticker: str, url: str = None) -> Dict[str, Any]:
        """
        Extract technical indicators for a single ticker using Twelve Data API.
        
        Args:
            ticker: Stock ticker symbol
            url: Not used (kept for compatibility)
            
        Returns:
            Dictionary containing extracted indicators and metadata
        """
        logger.info(f"Extracting indicators for {ticker} using Twelve Data API")
        
        result = {
            'Ticker': ticker,
            'source_url': f"Twelve Data API - {ticker}",
            'indicator_last_checked': datetime.now().isoformat(),
            'data_quality': 'api',
            'notes': 'Data from Twelve Data API'
        }
        
        # Add random delay to avoid rate limiting
        self._random_delay()
        
        if self.use_mock_data:
            logger.info(f"Using mock data for {ticker} (no API key)")
            indicators = self._generate_mock_indicators(ticker)
            result['data_quality'] = 'mock'
            result['notes'] = 'Mock data - No API key provided'
        else:
            try:
                indicators = {}
                
                # Get historical data for pivot points
                historical_data = self._get_historical_data(ticker, 10)
                if historical_data and 'values' in historical_data and len(historical_data['values']) > 0:
                    latest = historical_data['values'][0]
                    if all(key in latest for key in ['high', 'low', 'close']):
                        try:
                            high = float(latest['high'])
                            low = float(latest['low'])
                            close = float(latest['close'])
                            volume = int(float(latest.get('volume', 0)))
                            
                            pivot_data = self._calculate_pivot_points(high, low, close)
                            indicators.update(pivot_data)
                            indicators['Volume_daily'] = volume
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error parsing historical data for {ticker}: {e}")
                
                # Extract technical indicators using API
                indicators_to_fetch = [
                    ('ema', 'EMA20', {'time_period': '20'}),
                    ('sma', 'SMA50', {'time_period': '50'}),
                    ('rsi', 'RSI_14', {'time_period': '14'}),
                    ('adx', 'ADX_14', {'time_period': '14'}),
                    ('atr', 'ATR_14', {'time_period': '14'})
                ]
                
                for api_endpoint, indicator_name, params in indicators_to_fetch:
                    value = self._extract_technical_indicator(ticker, api_endpoint, **params)
                    if value is not None:
                        indicators[indicator_name] = value
                    else:
                        indicators[indicator_name] = 'N/A'
                
                # Special handling for MACD (multiple values)
                macd_data = self._make_api_request('macd', {
                    'symbol': ticker,
                    'interval': '1day',
                    'fast_period': '12',
                    'slow_period': '26',
                    'signal_period': '9'
                })
                
                if macd_data and 'values' in macd_data and len(macd_data['values']) > 0:
                    latest_macd = macd_data['values'][0]
                    try:
                        indicators['MACD_value'] = float(latest_macd.get('macd', 'N/A'))
                        indicators['MACD_signal'] = float(latest_macd.get('macd_signal', 'N/A'))
                        indicators['MACD_histogram'] = float(latest_macd.get('macd_hist', 'N/A'))
                    except (ValueError, TypeError):
                        indicators.update({
                            'MACD_value': 'N/A',
                            'MACD_signal': 'N/A',
                            'MACD_histogram': 'N/A'
                        })
                
                # Special handling for Bollinger Bands (multiple values)
                bb_data = self._make_api_request('bbands', {
                    'symbol': ticker,
                    'interval': '1day',
                    'time_period': '20',
                    'sd': '2'
                })
                
                if bb_data and 'values' in bb_data and len(bb_data['values']) > 0:
                    latest_bb = bb_data['values'][0]
                    try:
                        indicators['Bollinger_upper'] = float(latest_bb.get('upper_band', 'N/A'))
                        indicators['Bollinger_middle'] = float(latest_bb.get('middle_band', 'N/A'))
                        indicators['Bollinger_lower'] = float(latest_bb.get('lower_band', 'N/A'))
                    except (ValueError, TypeError):
                        indicators.update({
                            'Bollinger_upper': 'N/A',
                            'Bollinger_middle': 'N/A',
                            'Bollinger_lower': 'N/A'
                        })
                
                # Ensure all required indicators exist
                required_indicators = [
                    'Woodies_Pivot', 'Woodies_S1', 'Woodies_S2', 'Woodies_R1', 'Woodies_R2',
                    'EMA20', 'SMA50', 'RSI_14', 'MACD_value', 'MACD_signal', 'MACD_histogram',
                    'Bollinger_upper', 'Bollinger_middle', 'Bollinger_lower', 'Volume_daily',
                    'ADX_14', 'ATR_14'
                ]
                
                for indicator in required_indicators:
                    if indicator not in indicators:
                        indicators[indicator] = 'N/A'
                
                # Determine data quality
                meaningful_data = sum(1 for v in indicators.values() if v != 'N/A')
                if meaningful_data >= 10:
                    result['data_quality'] = 'excellent'
                elif meaningful_data >= 5:
                    result['data_quality'] = 'good'
                elif meaningful_data >= 1:
                    result['data_quality'] = 'partial'
                else:
                    result['data_quality'] = 'fallback'
                    indicators = self._generate_mock_indicators(ticker)
                    result['notes'] = 'API failed - using mock data'
                    
            except Exception as e:
                logger.error(f"Error extracting indicators for {ticker}: {e}")
                indicators = self._generate_mock_indicators(ticker)
                result['data_quality'] = 'mock'
                result['notes'] = f'Error: {str(e)} - using mock data'
        
        # Merge indicators into result
        result.update(indicators)
        
        logger.info(f"Extracted indicators for {ticker} with quality: {result['data_quality']}")
        return result
    
    def process_tickers_file(self, url_file: str, output_file: str) -> bool:
        """
        Process tickers from URL file and update output file with indicators.
        
        Args:
            url_file: Path to Excel file with ticker URLs (optional, only Ticker column needed)
            output_file: Path to output Excel file to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Processing tickers from {url_file}")
            
            # Load URL mappings - only need Ticker column now
            if not os.path.exists(url_file):
                logger.error(f"URL file not found: {url_file}")
                return False
                
            url_df = pd.read_excel(url_file)
            if 'Ticker' not in url_df.columns:
                logger.error("URL file must have a 'Ticker' column")
                return False
            
            # Load existing output file or create new one
            output_df = pd.DataFrame()
            if os.path.exists(output_file):
                try:
                    output_df = pd.read_excel(output_file)
                    logger.info(f"Loaded existing output file with {len(output_df)} rows")
                    
                    # Create backup
                    backup_file = f"{output_file.replace('.xlsx', '')}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    output_df.to_excel(backup_file, index=False)
                    logger.info(f"Created backup: {backup_file}")
                    
                except Exception as e:
                    logger.warning(f"Could not load existing output file: {e}")
                    output_df = pd.DataFrame()
            
            # Extract indicators for each ticker
            results = []
            tickers = url_df['Ticker'].tolist()
            
            logger.info(f"Processing {len(tickers)} tickers")
            
            for i, ticker in enumerate(tickers, 1):
                logger.info(f"Processing {ticker} ({i}/{len(tickers)})")
                
                try:
                    # URL is not needed for API-based extraction
                    result = self.extract_indicators_for_ticker(ticker)
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Failed to process {ticker}: {e}")
                    # Create fallback result
                    fallback_result = {
                        'Ticker': ticker,
                        'source_url': 'Failed',
                        'indicator_last_checked': datetime.now().isoformat(),
                        'data_quality': 'failed',
                        'notes': f'Processing failed: {str(e)}'
                    }
                    
                    # Add N/A for all indicators
                    for key in ['Woodies_Pivot', 'Woodies_S1', 'Woodies_S2', 'Woodies_R1', 'Woodies_R2',
                               'EMA20', 'SMA50', 'RSI_14', 'MACD_value', 'MACD_signal', 'MACD_histogram',
                               'Bollinger_upper', 'Bollinger_middle', 'Bollinger_lower', 'Volume_daily',
                               'ADX_14', 'ATR_14']:
                        fallback_result[key] = 'N/A'
                    results.append(fallback_result)
            
            # Convert results to DataFrame
            results_df = pd.DataFrame(results)
            
            # Merge with existing data
            if not output_df.empty and 'Ticker' in output_df.columns:
                # Merge on Ticker, updating existing rows and adding new ones
                output_df = output_df.set_index('Ticker')
                results_df = results_df.set_index('Ticker')
                
                # Update existing columns and add new ones
                for col in results_df.columns:
                    output_df[col] = results_df[col].combine_first(output_df.get(col))
                
                # Add new tickers
                new_tickers = results_df.index.difference(output_df.index)
                if len(new_tickers) > 0:
                    output_df = pd.concat([output_df, results_df.loc[new_tickers]])
                
                output_df = output_df.reset_index()
            else:
                output_df = results_df
            
            # Save results
            output_df.to_excel(output_file, index=False)
            logger.info(f"Successfully saved results to {output_file}")
            
            # Log summary
            quality_counts = results_df['data_quality'].value_counts()
            logger.info(f"Processing complete! Quality summary: {quality_counts.to_dict()}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing tickers file: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources (no-op for API-based extractor)."""
        logger.debug("Cleanup completed (no resources to clean)")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description='Extract technical indicators using Twelve Data API')
    parser.add_argument('--url-file', default='URL.xlsx', help='Excel file with tickers')
    parser.add_argument('--output-file', default='tickers.xlsx', help='Output Excel file')
    parser.add_argument('--api-key', help='Twelve Data API key (or set TWELVEDATA_API_KEY env var)')
    parser.add_argument('--delay-min', type=float, default=1.0, help='Minimum delay between requests')
    parser.add_argument('--delay-max', type=float, default=2.0, help='Maximum delay between requests')
    parser.add_argument('--limit', type=int, help='Limit number of tickers to process')
    # Keep these for backward compatibility
    parser.add_argument('--headless', action='store_true', default=True, help='Ignored (kept for compatibility)')
    parser.add_argument('--no-headless', action='store_false', dest='headless', help='Ignored (kept for compatibility)')
    parser.add_argument('--timeout', type=int, default=30, help='Ignored (kept for compatibility)')
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = TechnicalIndicatorsExtractor(
        api_key=args.api_key,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
    )
    
    try:
        # Process limited tickers if specified
        if args.limit:
            import pandas as pd
            url_df = pd.read_excel(args.url_file)
            if len(url_df) > args.limit:
                url_df = url_df.head(args.limit)
                limited_file = f"temp_limited_{args.limit}.xlsx"
                url_df.to_excel(limited_file, index=False)
                url_file = limited_file
            else:
                url_file = args.url_file
        else:
            url_file = args.url_file
        
        success = extractor.process_tickers_file(url_file, args.output_file)
        
        # Clean up temporary file
        if args.limit and 'limited_file' in locals():
            try:
                os.remove(limited_file)
            except:
                pass
        
        extractor.cleanup()
        
        if success:
            logger.info("✅ Technical indicators extraction completed successfully!")
            return 0
        else:
            logger.error("❌ Technical indicators extraction failed!")
            return 1
            
    except KeyboardInterrupt:
        logger.info("⏹️ Extraction interrupted by user")
        extractor.cleanup()
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        extractor.cleanup()
        return 1


if __name__ == "__main__":
    sys.exit(main())