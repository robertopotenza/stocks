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
import time
import socket
from collections import deque
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from technical_analysis import calculate_technical_levels
from logging_config import get_logger

# Get logger instance
logger = get_logger('stocks_app.stock_prices')

# Configuration variables - can be set via environment variables or modified here


def _normalize_api_key(value: Optional[str]) -> Optional[str]:
    """Return a cleaned API key or ``None`` when the value is effectively missing."""

    if not value:
        return None

    normalized = value.strip()
    if not normalized:
        return None

    placeholder_values = {
        "your_twelvedata_api_key",
        "your_api_key",
        "changeme",
        "replace_me",
    }

    lower_normalized = normalized.lower()
    if lower_normalized in placeholder_values or lower_normalized.startswith("your_"):
        return None

    return normalized


def _load_api_key_from_sources() -> Optional[str]:
    """Attempt to load the Twelve Data API key from multiple sources."""

    for candidate in (
        os.getenv("TWELVEDATA_API_KEY"),
        os.getenv("api_key"),
    ):
        normalized = _normalize_api_key(candidate)
        if normalized:
            return normalized

    # Try optional config module (if present) without raising import errors
    try:
        import config  # type: ignore

        return _normalize_api_key(getattr(config, "TWELVEDATA_API_KEY", None))
    except Exception:
        return None


TWELVEDATA_API_KEY = _load_api_key_from_sources()
TICKERS_FILE = os.getenv("TICKERS_FILE", "tickers.xlsx")

try:
    _REQUESTS_PER_MINUTE = int(os.getenv("TWELVEDATA_REQUESTS_PER_MINUTE", "8"))
except ValueError:
    _REQUESTS_PER_MINUTE = 8

try:
    _RATE_LIMIT_COOLDOWN_SECONDS = int(os.getenv("TWELVEDATA_RATE_LIMIT_COOLDOWN_SECONDS", "65"))
except ValueError:
    _RATE_LIMIT_COOLDOWN_SECONDS = 65

try:
    _RATE_LIMIT_RETRIES = int(os.getenv("TWELVEDATA_RATE_LIMIT_RETRIES", "3"))
except ValueError:
    _RATE_LIMIT_RETRIES = 3

_API_KEY_MISSING_LOGGED = False
_API_KEY_INVALID = False
_API_KEY_INVALID_LOGGED = False


class _MinuteRateLimiter:
    def __init__(self, limit: int, period_seconds: int = 60) -> None:
        self.limit = max(1, limit)
        self.period = max(1, period_seconds)
        self._timestamps: deque[float] = deque()
        self._cooldown_until: float = 0.0

    def wait_for_slot(self) -> None:
        while True:
            now = time.monotonic()

            if now < self._cooldown_until:
                sleep_time = self._cooldown_until - now
                logger.debug("Rate limiter cooling down for %.2f seconds", sleep_time)
                time.sleep(sleep_time)
                continue

            while self._timestamps and now - self._timestamps[0] >= self.period:
                self._timestamps.popleft()

            if len(self._timestamps) < self.limit:
                self._timestamps.append(now)
                return

            oldest = self._timestamps[0]
            sleep_time = self.period - (now - oldest)
            if sleep_time > 0:
                logger.debug("Rate limiter sleeping for %.2f seconds to respect quota", sleep_time)
                time.sleep(sleep_time)

    def impose_cooldown(self, seconds: int) -> None:
        seconds = max(0, seconds)
        if seconds == 0:
            return
        self._cooldown_until = max(self._cooldown_until, time.monotonic() + seconds)
        logger.info("⏳ Cooling down Twelve Data requests for %s seconds", seconds)


_TWELVEDATA_RATE_LIMITER = _MinuteRateLimiter(_REQUESTS_PER_MINUTE)


def check_dns_resolution(hostname: str) -> bool:
    """
    Check if DNS resolution works for a hostname.
    
    Args:
        hostname: The hostname to resolve
        
    Returns:
        True if DNS resolution succeeds, False otherwise
    """
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.gaierror:
        return False


def make_api_request_with_retry(url: str, params: Dict[str, Any], max_retries: int = 3) -> Optional[requests.Response]:
    """
    Make API request with retry logic and enhanced error handling.
    
    Args:
        url: The API endpoint URL
        params: Request parameters
        max_retries: Maximum number of retry attempts
        
    Returns:
        Response object if successful, None if all retries failed
    """
    import urllib.parse
    
    # Extract hostname for diagnostics
    parsed_url = urllib.parse.urlparse(url)
    hostname = parsed_url.netloc
    
    # Check DNS resolution first
    if not check_dns_resolution(hostname):
        logger.error(f"❌ DNS resolution failed for {hostname}")
        logger.error(f"💡 This is likely a network/DNS configuration issue in the production environment.")
        logger.error(f"💡 Possible solutions:")
        logger.error(f"   - Check DNS servers in /etc/resolv.conf")
        logger.error(f"   - Set DNS_SERVER environment variable")
        logger.error(f"   - Configure corporate proxy if behind firewall")
        return None
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"API request attempt {attempt + 1}/{max_retries} to {url}")
            _TWELVEDATA_RATE_LIMITER.wait_for_slot()
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                # Rate limiting - wait longer before retry
                wait_time = (2 ** attempt) * 2  # Exponential backoff starting at 2 seconds
                logger.warning(f"Rate limited (429). Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                _TWELVEDATA_RATE_LIMITER.impose_cooldown(wait_time)
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"API returned status {response.status_code}: {response.text}")
                if attempt == max_retries - 1:  # Last attempt
                    return None
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error on attempt {attempt + 1}/{max_retries}: {e}")
            if "Failed to resolve" in str(e) or "Name or service not known" in str(e):
                logger.error(f"💡 DNS resolution issue detected. Check network configuration.")
                return None  # Don't retry DNS issues
        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error on attempt {attempt + 1}/{max_retries}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}/{max_retries}: {e}")
        
        if attempt < max_retries - 1:
            wait_time = (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
            logger.info(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    logger.error(f"All {max_retries} attempts failed for {url}")
    return None


def _api_key_configured() -> bool:
    return TWELVEDATA_API_KEY is not None and not _API_KEY_INVALID


def _log_missing_api_key_hint() -> None:
    global _API_KEY_MISSING_LOGGED

    if _API_KEY_MISSING_LOGGED:
        return

    logger.warning("⚠️ No Twelve Data API key configured!")
    logger.warning("Set TWELVEDATA_API_KEY environment variable with your API key")
    logger.warning("Get your free API key from: https://twelvedata.com/")
    logger.info("Example:")
    logger.info("   export TWELVEDATA_API_KEY=your_api_key_here")
    logger.warning("Proceeding with mock data for testing...")
    _API_KEY_MISSING_LOGGED = True


def _mark_api_key_invalid(message: str) -> None:
    global _API_KEY_INVALID, _API_KEY_INVALID_LOGGED

    if not _API_KEY_INVALID:
        _API_KEY_INVALID = True

    if _API_KEY_INVALID_LOGGED:
        return

    logger.error("🚫 Twelve Data rejected the configured API key: %s", message)
    logger.error("💡 Switching to mock data for the remainder of this run.")
    logger.info("👉 Update the TWELVEDATA_API_KEY environment variable with a valid key from https://twelvedata.com/pricing")
    _API_KEY_INVALID_LOGGED = True


def _is_api_key_error(message: str) -> bool:
    lowered = message.lower()
    if "api key" not in lowered and "apikey" not in lowered:
        return False

    keywords = ["missing", "not specified", "invalid", "incorrect", "denied"]
    return any(keyword in lowered for keyword in keywords)


def _is_rate_limit_error(message: str) -> bool:
    lowered = message.lower()
    return "run out of api credits" in lowered or "api credits were used" in lowered or "rate limit" in lowered


def _handle_rate_limit(message: str) -> None:
    logger.warning("⏱️ Twelve Data rate limit reached: %s", message)
    _TWELVEDATA_RATE_LIMITER.impose_cooldown(_RATE_LIMIT_COOLDOWN_SECONDS)


def _handle_twelvedata_error(ticker: str, context: str, payload: Dict[str, Any]) -> str:
    """Return an error category for further handling."""

    message = str(payload.get("message") or payload.get("note") or payload)
    logger.error(f"API error for {ticker} {context}: {message}")

    if _is_api_key_error(message):
        _mark_api_key_invalid(message)
        return "api_key"

    if _is_rate_limit_error(message):
        _handle_rate_limit(message)
        return "rate_limit"

    return "other"


def _fetch_twelvedata_payload(
    ticker: str,
    context: str,
    url: str,
    params: Dict[str, Any],
    max_rate_limit_retries: int,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    for attempt in range(max_rate_limit_retries + 1):
        response = make_api_request_with_retry(url, params)
        if not response or response.status_code != 200:
            return None, "request_failed"

        try:
            payload = response.json()
        except (ValueError, TypeError) as exc:
            logger.error(f"Error parsing {context} data for {ticker}: {exc}")
            return None, "parse_error"

        if isinstance(payload, dict) and payload.get("status") == "error":
            category = _handle_twelvedata_error(ticker, context, payload)
            if category == "api_key":
                return None, "api_key"
            if category == "rate_limit" and attempt < max_rate_limit_retries:
                logger.info(
                    "Retrying %s request for %s after rate limit cooldown (%d/%d)",
                    context,
                    ticker,
                    attempt + 1,
                    max_rate_limit_retries,
                )
                continue
            return None, "api_error"

        if isinstance(payload, dict):
            logger.debug(f"{context.capitalize()} API response for {ticker}: {payload}")

        return payload, None

    return None, "rate_limit"


def get_stock_data_from_api(ticker: str) -> Dict[str, Any]:
    """
    Fetch stock data from Twelve Data API.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary containing stock data
    """
    if not _api_key_configured():
        if TWELVEDATA_API_KEY is None:
            _log_missing_api_key_hint()
        return get_mock_stock_data(ticker)

    logger.info(f"🔄 Fetching data for {ticker} from Twelve Data API...")
    
    try:
        # Get current price
        price_url = "https://api.twelvedata.com/price" 
        price_params = {
            'symbol': ticker,
            'apikey': TWELVEDATA_API_KEY
        }
        
        price_data, price_error = _fetch_twelvedata_payload(
            ticker,
            "price",
            price_url,
            price_params,
            _RATE_LIMIT_RETRIES,
        )
        current_price = None

        if price_error == "api_key":
            return get_mock_stock_data(ticker)

        if isinstance(price_data, dict) and 'price' in price_data:
            try:
                current_price = float(price_data['price'])
                logger.info(f"✅ Got price for {ticker}: ${current_price:.2f}")
            except (ValueError, TypeError, KeyError) as e:
                logger.error(f"Error parsing price data for {ticker}: {e}")
        elif price_error:
            logger.error(f"❌ Failed to get price data for {ticker} ({price_error})")
        elif price_data is not None:
            logger.warning(f"No 'price' field in response for {ticker}: {price_data}")
        
        # Get quote data for additional information
        quote_url = "https://api.twelvedata.com/quote"
        quote_params = {
            'symbol': ticker,
            'apikey': TWELVEDATA_API_KEY
        }
        
        quote_data, quote_error = _fetch_twelvedata_payload(
            ticker,
            "quote",
            quote_url,
            quote_params,
            _RATE_LIMIT_RETRIES,
        )

        if quote_error == "api_key":
            return get_mock_stock_data(ticker)

        if not isinstance(quote_data, dict):
            quote_data = {}
            if quote_error:
                logger.warning(f"Failed to get quote data for {ticker} ({quote_error})")
        else:
            logger.debug(f"Quote API response for {ticker}: {quote_data}")
        
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

        resolved_price: Optional[float] = None

        if isinstance(current_price, (int, float)):
            resolved_price = current_price
        elif isinstance(quote_data, dict):
            close_value = quote_data.get('close')
            try:
                resolved_price = float(close_value) if close_value is not None else None
            except (ValueError, TypeError):
                resolved_price = None

        if resolved_price is not None:
            stock_data['Current_Price'] = resolved_price

        # Calculate additional metrics if we have price data
        if resolved_price is not None:
            try:
                # Calculate technical levels using the existing function
                technical_levels = calculate_technical_levels(ticker)
                stock_data.update(technical_levels)
            except Exception as e:
                logger.warning(f"Could not calculate technical levels for {ticker}: {e}")

        # Log final result
        if resolved_price is not None:
            logger.info(f"✅ Successfully fetched data for {ticker}: ${resolved_price:.2f}")
        else:
            logger.error(f"❌ No price data obtained for {ticker}, falling back to mock data")
            return get_mock_stock_data(ticker)

        return stock_data
        
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching data for {ticker}: {e}")
        logger.error(f"💡 Falling back to mock data for {ticker}")
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
        technical_levels = calculate_technical_levels(ticker)
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
    if TWELVEDATA_API_KEY is None:
        _log_missing_api_key_hint()
    
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
    if TWELVEDATA_API_KEY is None or _API_KEY_INVALID:
        logger.info("💡 Note: Mock data was used. Configure a valid Twelve Data API key for real data.")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()