#!/usr/bin/env python3
"""
Technical Indicators Extractor Module

This module extracts technical indicators from web pages using headless browser automation.
It supports extraction of:
- Woodie's Pivot Points (Pivot, S1, S2, R1, R2)
- Moving Averages: EMA20, SMA50
- RSI (14)
- MACD (value/histogram/signal)
- Bollinger Bands (upper, middle, lower)
- Volume (daily)
- ADX(14)
- ATR(14)

Designed for reliability with multiple extraction strategies and robust error handling.
"""

import pandas as pd
import os
import sys
import re
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from logging_config import get_logger

# Get logger instance
logger = get_logger('stocks_app.technical_indicators')


class TechnicalIndicatorsExtractor:
    """
    Main class for extracting technical indicators from web pages.
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30, delay_min: float = 0.5, delay_max: float = 2.0, 
                 enable_selenium: bool = True):
        """
        Initialize the extractor with configuration.
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in seconds
            delay_min: Minimum delay between requests (seconds)
            delay_max: Maximum delay between requests (seconds)
            enable_selenium: Enable Selenium fallback (default True)
        """
        self.headless = headless
        self.timeout = timeout
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.enable_selenium = enable_selenium
        self.user_agent = UserAgent()
        self.driver = None
        self.page_cache = {}
        self.current_header_profile = 0
        
        # Set up requests session with retry strategy
        self.session = self._setup_requests_session()
        
        # Header profiles for rotation to avoid detection
        self.header_profiles = self._get_header_profiles()
        
    def _setup_requests_session(self) -> requests.Session:
        """Set up requests session with retry strategy and proxy support."""
        session = requests.Session()
        
        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # 'method_whitelist' was renamed to 'allowed_methods' in urllib3 v1.26.0
            backoff_factor=1,
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Configure proxy settings from environment variables
        http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
        
        if http_proxy or https_proxy:
            proxies = {}
            if http_proxy:
                proxies['http'] = http_proxy
                logger.info(f"Using HTTP proxy: {http_proxy}")
            if https_proxy:
                proxies['https'] = https_proxy
                logger.info(f"Using HTTPS proxy: {https_proxy}")
            session.proxies.update(proxies)
        
        return session
    
    def _get_header_profiles(self) -> List[Dict[str, str]]:
        """Get multiple realistic browser header profiles for rotation."""
        base_referers = [
            'https://www.google.com/',
            'https://www.investing.com/',
            'https://finance.yahoo.com/',
            'https://www.bloomberg.com/',
            'https://www.marketwatch.com/'
        ]
        
        profiles = []
        
        # Chrome profiles
        for i in range(3):
            ua = self.user_agent.chrome
            profiles.append({
                'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Cache-Control': 'max-age=0',
                'Referer': random.choice(base_referers)
            })
        
        # Firefox profiles  
        for i in range(2):
            ua = self.user_agent.firefox
            profiles.append({
                'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': random.choice(base_referers)
            })
            
        # Safari profiles
        ua = self.user_agent.safari
        profiles.append({
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': random.choice(base_referers)
        })
        
        return profiles
        
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with profile rotation."""
        # Rotate through header profiles to avoid detection
        headers = self.header_profiles[self.current_header_profile].copy()
        self.current_header_profile = (self.current_header_profile + 1) % len(self.header_profiles)
        
        logger.debug(f"Using header profile {self.current_header_profile} with User-Agent: {headers['User-Agent']}")
        return headers
    
    def _setup_selenium_driver(self) -> Optional[webdriver.Chrome]:
        """Set up Selenium Chrome driver with enhanced options for container environments."""
        if not self.enable_selenium:
            logger.debug("Selenium disabled by configuration")
            return None
            
        try:
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
            
            options = Options()
            
            # Essential options for headless container operation
            if self.headless:
                options.add_argument('--headless=new')  # Use new headless mode
            
            # Security and stability options for containers
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-ipc-flooding-protection')
            
            # Window size and display options
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')
            
            # Network and performance options
            options.add_argument('--enable-automation')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # Speed up by not loading images
            
            # Anti-detection measures
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2
            })
            
            # Set a realistic user agent
            user_agent = self.user_agent.chrome
            options.add_argument(f'--user-agent={user_agent}')
            
            # Try to find Chrome/Chromium binary
            chrome_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable', 
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/snap/bin/chromium'
            ]
            
            chrome_binary = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    break
                    
            if chrome_binary:
                options.binary_location = chrome_binary
                logger.debug(f"Using Chrome binary: {chrome_binary}")
            else:
                logger.warning("No Chrome binary found, relying on default PATH")
            
            # Try to create driver with different approaches
            driver = None
            
            # First try: default ChromeDriver
            try:
                driver = webdriver.Chrome(options=options)
                logger.info("✅ Chrome WebDriver initialized successfully")
            
            except Exception as e1:
                logger.debug(f"Default ChromeDriver failed: {e1}")
                
                # Second try: undetected-chromedriver if available
                try:
                    import undetected_chromedriver as uc
                    driver = uc.Chrome(
                        options=options,
                        headless=self.headless,
                        version_main=None  # Auto-detect version
                    )
                    logger.info("✅ Undetected Chrome WebDriver initialized successfully")
                    
                except ImportError:
                    logger.debug("undetected-chromedriver not available")
                except Exception as e2:
                    logger.debug(f"Undetected ChromeDriver failed: {e2}")
            
            if driver:
                # Configure timeouts
                driver.set_page_load_timeout(self.timeout)
                driver.implicitly_wait(10)
                
                # Execute script to hide automation indicators
                try:
                    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                except Exception:
                    pass  # Ignore if script execution fails
                
                logger.debug("Selenium driver configured successfully")
                return driver
            else:
                logger.error("❌ Failed to initialize any Chrome WebDriver")
                return None
                
        except ImportError as e:
            logger.error(f"Selenium dependencies missing: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to setup Selenium driver: {e}")
            return None
    
    def _random_delay(self, retry_count: int = 0):
        """Add random delay between requests with exponential backoff on retries."""
        base_delay = random.uniform(self.delay_min, self.delay_max)
        # Add exponential backoff for retries
        if retry_count > 0:
            backoff_delay = (2 ** retry_count) * base_delay
            delay = min(backoff_delay, 30)  # Cap at 30 seconds
            logger.debug(f"Retry {retry_count}: Adding backoff delay of {delay:.2f}s")
        else:
            delay = base_delay
            
        time.sleep(delay)
    
    def _extract_with_requests(self, url: str) -> Optional[BeautifulSoup]:
        """
        Extract page content using requests with enhanced resilience.
        
        Args:
            url: URL to extract from
            
        Returns:
            BeautifulSoup object or None if failed
        """
        if url in self.page_cache:
            logger.debug(f"Using cached content for {url}")
            return self.page_cache[url]
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                headers = self._get_headers()
                
                logger.info(f"📡 Attempt {attempt + 1}/{max_retries}: Fetching {url}")
                logger.debug(f"Request headers: {headers}")
                logger.debug(f"Timeout: {self.timeout}s")
                
                # Add random delay with exponential backoff for retries
                if attempt > 0:
                    self._random_delay(retry_count=attempt)
                else:
                    self._random_delay()
                
                response = self.session.get(url, headers=headers, timeout=self.timeout)
                
                # Handle different response status codes
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    self.page_cache[url] = soup
                    
                    logger.debug(f"✅ Successfully fetched {url}")
                    logger.debug(f"Response status: {response.status_code}, Content length: {len(response.text)}")
                    return soup
                    
                elif response.status_code == 403:
                    logger.warning(f"🚫 Access BLOCKED (403) for {url} - Bot detection/Rate limiting")
                    logger.warning(f"User-Agent used: {headers.get('User-Agent', 'Unknown')}")
                    logger.warning("This is server-side blocking, not DNS failure")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying with different header profile in attempt {attempt + 2}")
                        continue
                    else:
                        logger.warning("All request attempts failed with 403, trying Selenium fallback...")
                        return self._extract_with_selenium(url) if self.enable_selenium else None
                        
                elif response.status_code == 429:
                    logger.warning(f"⏳ Rate limited (429) for {url}")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)
                        logger.info(f"Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Rate limit exceeded on all attempts")
                        return None
                        
                else:
                    logger.warning(f"HTTP error {response.status_code} for {url}")
                    if attempt < max_retries - 1:
                        continue
                    return None
                    
            except requests.exceptions.ConnectionError as e:
                # Enhanced DNS/connection error reporting
                error_str = str(e)
                if "Failed to resolve" in error_str or "Name or service not known" in error_str:
                    logger.error(f"DNS Resolution Failed for {url}: {e}")
                    logger.error("Possible causes: DNS server misconfiguration, network restrictions, or firewall blocking")
                    logger.error("Suggested fixes:")
                    logger.error("  1. Add to /etc/hosts: echo '5.254.205.57 www.investing.com investing.com' >> /etc/hosts")
                    logger.error("  2. Configure DNS: export DNS_SERVER=8.8.8.8")
                    logger.error("  3. Check proxy settings: export HTTPS_PROXY=http://proxy:port")
                else:
                    logger.error(f"Connection error for {url}: {e}")
                    
                if attempt < max_retries - 1:
                    logger.info(f"Retrying connection in attempt {attempt + 2}")
                    continue
                return None
                
            except requests.exceptions.Timeout as e:
                logger.warning(f"⏱️ Timeout fetching {url} after {self.timeout}s: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying with longer timeout in attempt {attempt + 2}")
                    continue
                return None
                
            except Exception as e:
                logger.warning(f"Unexpected error fetching {url}: {type(e).__name__}: {e}")
                if attempt < max_retries - 1:
                    continue
                return None
                
        logger.error(f"All {max_retries} attempts failed for {url}")
        return None
    
    def _extract_with_selenium(self, url: str) -> Optional[BeautifulSoup]:
        """
        Extract page content using Selenium for JS-rendered content.
        
        Args:
            url: URL to extract from
            
        Returns:
            BeautifulSoup object or None if failed
        """
        # Skip Selenium if no network access or driver unavailable
        if not self.driver:
            self.driver = self._setup_selenium_driver()
            if not self.driver:
                logger.info("🚫 Selenium driver not available, skipping Selenium method")
                return None
        
        if url in self.page_cache:
            logger.debug(f"Using cached content for {url}")
            return self.page_cache[url]
            
        try:
            logger.info(f"🤖 Attempting to fetch {url} using Selenium WebDriver")
            self.driver.get(url)
            
            # Wait for page to load with shorter timeout
            WebDriverWait(self.driver, min(self.timeout, 15)).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Shorter wait for dynamic content
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            self.page_cache[url] = soup
            
            logger.debug(f"Successfully fetched {url} with Selenium")
            return soup
            
        except Exception as e:
            logger.warning(f"Failed to fetch {url} with Selenium: {e}")
            return None
    
    def _extract_numeric_value(self, text: str, pattern: str) -> Optional[float]:
        """
        Extract numeric value from text using regex pattern.
        
        Args:
            text: Text to search in
            pattern: Regex pattern to match
            
        Returns:
            Extracted float value or None
        """
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(',', '').replace('%', '')
                return float(value_str)
        except Exception as e:
            logger.debug(f"Failed to extract numeric value with pattern '{pattern}': {e}")
        return None
    
    def _extract_indicators_investing_com(self, soup: BeautifulSoup, ticker: str) -> Dict[str, Any]:
        """
        Extract technical indicators from investing.com page.
        
        Args:
            soup: BeautifulSoup object of the page
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary of extracted indicators
        """
        indicators = {
            'Woodies_Pivot': 'N/A',
            'Woodies_S1': 'N/A',
            'Woodies_S2': 'N/A',
            'Woodies_R1': 'N/A',
            'Woodies_R2': 'N/A',
            'EMA20': 'N/A',
            'SMA50': 'N/A',
            'RSI_14': 'N/A',
            'MACD_value': 'N/A',
            'MACD_signal': 'N/A',
            'MACD_histogram': 'N/A',
            'Bollinger_upper': 'N/A',
            'Bollinger_middle': 'N/A',
            'Bollinger_lower': 'N/A',
            'Volume_daily': 'N/A',
            'ADX_14': 'N/A',
            'ATR_14': 'N/A'
        }
        
        try:
            page_text = soup.get_text()
            
            # Extract RSI (14)
            rsi_patterns = [
                r'RSI\s*\(14\)[:\s]*([0-9]{1,3}\.?[0-9]*)',
                r'RSI[:\s]*([0-9]{1,3}\.?[0-9]*)',
                r'Relative\s+Strength\s+Index[:\s]*([0-9]{1,3}\.?[0-9]*)'
            ]
            for pattern in rsi_patterns:
                value = self._extract_numeric_value(page_text, pattern)
                if value is not None:
                    indicators['RSI_14'] = value
                    break
            
            # Extract Moving Averages
            ema20_patterns = [
                r'EMA\s*\(20\)[:\s]*([0-9,\.]+)',
                r'EMA20[:\s]*([0-9,\.]+)',
                r'Exponential\s+Moving\s+Average\s+20[:\s]*([0-9,\.]+)'
            ]
            for pattern in ema20_patterns:
                value = self._extract_numeric_value(page_text, pattern)
                if value is not None:
                    indicators['EMA20'] = value
                    break
            
            sma50_patterns = [
                r'SMA\s*\(50\)[:\s]*([0-9,\.]+)',
                r'SMA50[:\s]*([0-9,\.]+)',
                r'Simple\s+Moving\s+Average\s+50[:\s]*([0-9,\.]+)'
            ]
            for pattern in sma50_patterns:
                value = self._extract_numeric_value(page_text, pattern)
                if value is not None:
                    indicators['SMA50'] = value
                    break
            
            # Extract MACD
            macd_patterns = [
                r'MACD[:\s]*([+-]?[0-9,\.]+)',
                r'MACD\s+Line[:\s]*([+-]?[0-9,\.]+)'
            ]
            for pattern in macd_patterns:
                value = self._extract_numeric_value(page_text, pattern)
                if value is not None:
                    indicators['MACD_value'] = value
                    break
            
            # Extract Bollinger Bands
            bb_upper_patterns = [
                r'Bollinger\s+Upper[:\s]*([0-9,\.]+)',
                r'BB\s+Upper[:\s]*([0-9,\.]+)',
                r'Upper\s+Band[:\s]*([0-9,\.]+)'
            ]
            for pattern in bb_upper_patterns:
                value = self._extract_numeric_value(page_text, pattern)
                if value is not None:
                    indicators['Bollinger_upper'] = value
                    break
                    
            bb_lower_patterns = [
                r'Bollinger\s+Lower[:\s]*([0-9,\.]+)',
                r'BB\s+Lower[:\s]*([0-9,\.]+)',
                r'Lower\s+Band[:\s]*([0-9,\.]+)'
            ]
            for pattern in bb_lower_patterns:
                value = self._extract_numeric_value(page_text, pattern)
                if value is not None:
                    indicators['Bollinger_lower'] = value
                    break
            
            # Extract Volume
            volume_patterns = [
                r'Volume[:\s]*([0-9,\.]+[KMB]?)',
                r'Daily\s+Volume[:\s]*([0-9,\.]+[KMB]?)'
            ]
            for pattern in volume_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    volume_str = match.group(1).replace(',', '')
                    # Handle K, M, B suffixes
                    if volume_str.endswith('K'):
                        value = float(volume_str[:-1]) * 1000
                    elif volume_str.endswith('M'):
                        value = float(volume_str[:-1]) * 1000000
                    elif volume_str.endswith('B'):
                        value = float(volume_str[:-1]) * 1000000000
                    else:
                        value = float(volume_str)
                    indicators['Volume_daily'] = value
                    break
            
            # Extract ADX
            adx_patterns = [
                r'ADX\s*\(14\)[:\s]*([0-9,\.]+)',
                r'ADX[:\s]*([0-9,\.]+)',
                r'Average\s+Directional\s+Index[:\s]*([0-9,\.]+)'
            ]
            for pattern in adx_patterns:
                value = self._extract_numeric_value(page_text, pattern)
                if value is not None:
                    indicators['ADX_14'] = value
                    break
            
            # Extract ATR
            atr_patterns = [
                r'ATR\s*\(14\)[:\s]*([0-9,\.]+)',
                r'ATR[:\s]*([0-9,\.]+)',
                r'Average\s+True\s+Range[:\s]*([0-9,\.]+)'
            ]
            for pattern in atr_patterns:
                value = self._extract_numeric_value(page_text, pattern)
                if value is not None:
                    indicators['ATR_14'] = value
                    break
            
            # Try to extract pivot points from structured data
            self._extract_pivot_points(soup, indicators)
            
        except Exception as e:
            logger.error(f"Error extracting indicators for {ticker}: {e}")
        
        return indicators
    
    def _generate_mock_indicators(self, ticker: str) -> Dict[str, Any]:
        """
        Generate mock technical indicators for testing when network is unavailable.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary of mock indicators
        """
        import hashlib
        
        # Use ticker hash to generate consistent but varied mock data
        hash_val = int(hashlib.md5(ticker.encode()).hexdigest()[:8], 16)
        
        # Generate mock values based on hash for consistency
        mock_price = 100 + (hash_val % 500)  # Price between 100-600
        
        return {
            'Woodies_Pivot': round(mock_price + (hash_val % 20) - 10, 2),
            'Woodies_S1': round(mock_price - 15 - (hash_val % 10), 2),
            'Woodies_S2': round(mock_price - 25 - (hash_val % 15), 2),
            'Woodies_R1': round(mock_price + 15 + (hash_val % 10), 2),
            'Woodies_R2': round(mock_price + 25 + (hash_val % 15), 2),
            'EMA20': round(mock_price + (hash_val % 10) - 5, 2),
            'SMA50': round(mock_price + (hash_val % 12) - 6, 2),
            'RSI_14': round(30 + (hash_val % 40), 1),  # RSI between 30-70
            'MACD_value': round((hash_val % 20) - 10, 3),  # MACD between -10 and 10
            'MACD_signal': round((hash_val % 15) - 7.5, 3),
            'MACD_histogram': round((hash_val % 8) - 4, 3),
            'Bollinger_upper': round(mock_price + 20 + (hash_val % 10), 2),
            'Bollinger_middle': round(mock_price, 2),
            'Bollinger_lower': round(mock_price - 20 - (hash_val % 10), 2),
            'Volume_daily': (hash_val % 10000000) + 1000000,  # Volume between 1M-11M
            'ADX_14': round(20 + (hash_val % 50), 1),  # ADX between 20-70
            'ATR_14': round(1 + (hash_val % 10), 2)  # ATR between 1-11
        }
        """
        Extract Woodie's Pivot Points from page structure.
        
        Args:
            soup: BeautifulSoup object
            indicators: Dictionary to update with pivot points
        """
        try:
            # Look for pivot points table or structure
            pivot_tables = soup.find_all('table', class_=re.compile(r'pivot|technical', re.I))
            
            for table in pivot_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text().strip().lower()
                        value_text = cells[1].get_text().strip()
                        
                        try:
                            value = float(value_text.replace(',', ''))
                            
                            if 'pivot' in label or 'pp' in label:
                                indicators['Woodies_Pivot'] = value
                            elif 's1' in label or 'support 1' in label:
                                indicators['Woodies_S1'] = value
                            elif 's2' in label or 'support 2' in label:
                                indicators['Woodies_S2'] = value
                            elif 'r1' in label or 'resistance 1' in label:
                                indicators['Woodies_R1'] = value
                            elif 'r2' in label or 'resistance 2' in label:
                                indicators['Woodies_R2'] = value
                        except ValueError:
                            continue
                            
        except Exception as e:
            logger.debug(f"Failed to extract pivot points from table structure: {e}")
    
    def _extract_pivot_points(self, soup: BeautifulSoup, indicators: Dict[str, Any]):
        """
        Extract Woodie's Pivot Points from page structure.
        
        Args:
            soup: BeautifulSoup object
            indicators: Dictionary to update with pivot points
        """
        try:
            # Look for pivot points table or structure
            pivot_tables = soup.find_all('table', class_=re.compile(r'pivot|technical', re.I))
            
            for table in pivot_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text().strip().lower()
                        value_text = cells[1].get_text().strip()
                        
                        try:
                            value = float(value_text.replace(',', ''))
                            
                            if 'pivot' in label or 'pp' in label:
                                indicators['Woodies_Pivot'] = value
                            elif 's1' in label or 'support 1' in label:
                                indicators['Woodies_S1'] = value
                            elif 's2' in label or 'support 2' in label:
                                indicators['Woodies_S2'] = value
                            elif 'r1' in label or 'resistance 1' in label:
                                indicators['Woodies_R1'] = value
                            elif 'r2' in label or 'resistance 2' in label:
                                indicators['Woodies_R2'] = value
                        except ValueError:
                            continue
                            
        except Exception as e:
            logger.debug(f"Failed to extract pivot points from table structure: {e}")
    
    def extract_indicators_for_ticker(self, ticker: str, url: str) -> Dict[str, Any]:
        """
        Extract technical indicators for a single ticker.
        
        Args:
            ticker: Stock ticker symbol
            url: URL to extract from
            
        Returns:
            Dictionary containing extracted indicators and metadata
        """
        logger.info(f"Extracting indicators for {ticker} from {url}")
        
        result = {
            'Ticker': ticker,
            'source_url': url,
            'indicator_last_checked': datetime.now().isoformat(),
            'data_quality': 'fallback',
            'notes': ''
        }
        
        # Add random delay
        self._random_delay()
        
        # Try extraction methods in order of preference
        soup = None
        
        # First try with requests (faster)
        logger.info(f"🌐 Attempting to extract {ticker} using HTTP requests method")
        soup = self._extract_with_requests(url)
        if soup:
            logger.info(f"✅ HTTP requests method successful for {ticker}")
            indicators = self._extract_indicators_investing_com(soup, ticker)
            # Check if we got meaningful data
            meaningful_data = sum(1 for v in indicators.values() if v != 'N/A')
            if meaningful_data >= 3:
                result['data_quality'] = 'good'
            elif meaningful_data >= 1:
                result['data_quality'] = 'partial'
        else:
            # Fallback to Selenium
            logger.info(f"❌ HTTP requests method failed for {ticker}, attempting Selenium method")
            soup = self._extract_with_selenium(url)
            if soup:
                logger.info(f"✅ Selenium method successful for {ticker}")
                indicators = self._extract_indicators_investing_com(soup, ticker)
                meaningful_data = sum(1 for v in indicators.values() if v != 'N/A')
                if meaningful_data >= 3:
                    result['data_quality'] = 'good'
                elif meaningful_data >= 1:
                    result['data_quality'] = 'partial'
                result['notes'] = 'Used Selenium fallback'
            else:
                # Network failure - use mock data for testing
                logger.info(f"❌ Selenium method failed for {ticker}, falling back to mock data")
                logger.warning(f"Network unavailable for {ticker}, using mock data for testing")
                logger.warning("This indicates a production issue that needs immediate attention:")
                logger.warning("  1. DNS resolution failure for investing.com")
                logger.warning("  2. Network connectivity problems")
                logger.warning("  3. Firewall or proxy configuration issues")
                logger.warning("Run 'python production_debug.py' for detailed diagnosis")
                
                indicators = self._generate_mock_indicators(ticker)
                result['data_quality'] = 'mock'
                result['notes'] = 'Mock data - PRODUCTION ISSUE: Network/DNS failure. Run production_debug.py for fixes.'
        
        # Merge indicators into result
        result.update(indicators)
        
        logger.info(f"Extracted indicators for {ticker} with quality: {result['data_quality']}")
        return result
    
    def process_tickers_file(self, url_file: str, output_file: str) -> bool:
        """
        Process all tickers from URL file and update output file.
        
        Args:
            url_file: Path to Excel file with tickers and URLs
            output_file: Path to Excel file to update with indicators
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load URL mappings
            logger.info(f"Loading URL mappings from {url_file}")
            url_df = pd.read_excel(url_file)
            
            if 'Ticker' not in url_df.columns or 'URL' not in url_df.columns:
                logger.error(f"Required columns 'Ticker' and 'URL' not found in {url_file}")
                return False
            
            # Load existing tickers file or create new one
            if os.path.exists(output_file):
                logger.info(f"Loading existing data from {output_file}")
                # Create backup
                backup_file = f"{output_file.replace('.xlsx', '')}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                import shutil
                shutil.copy2(output_file, backup_file)
                logger.info(f"Created backup at {backup_file}")
                
                output_df = pd.read_excel(output_file)
            else:
                logger.info(f"Creating new output file {output_file}")
                output_df = pd.DataFrame()
            
            # Process each ticker
            results = []
            total_tickers = len(url_df)
            
            for idx, row in url_df.iterrows():
                ticker = row['Ticker']
                url = row['URL']
                
                logger.info(f"Processing {idx + 1}/{total_tickers}: {ticker}")
                
                try:
                    result = self.extract_indicators_for_ticker(ticker, url)
                    results.append(result)
                    
                    # Progress logging
                    if (idx + 1) % 10 == 0:
                        logger.info(f"Processed {idx + 1}/{total_tickers} tickers")
                        
                except Exception as e:
                    logger.error(f"Failed to process {ticker}: {e}")
                    # Add fallback result
                    fallback_result = {
                        'Ticker': ticker,
                        'source_url': url,
                        'indicator_last_checked': datetime.now().isoformat(),
                        'data_quality': 'fallback',
                        'notes': f'Processing error: {str(e)}'
                    }
                    # Add all indicator columns with N/A
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
                    output_df[col] = results_df[col]
                
                output_df = output_df.reset_index()
            else:
                output_df = results_df
            
            # Save updated file
            output_df.to_excel(output_file, index=False)
            logger.info(f"Successfully saved {len(results)} ticker results to {output_file}")
            
            # Summary statistics
            quality_counts = results_df['data_quality'].value_counts()
            logger.info(f"Data Quality Summary: {dict(quality_counts)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing tickers file: {e}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
        self.page_cache.clear()


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description='Extract technical indicators from web pages')
    parser.add_argument('--url-file', default='URL.xlsx',
                       help='Excel file with Ticker and URL columns (default: URL.xlsx)')
    parser.add_argument('--output-file', default='tickers.xlsx',
                       help='Excel file to update with indicators (default: tickers.xlsx)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    parser.add_argument('--no-headless', action='store_false', dest='headless',
                       help='Run browser with visible interface')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Page load timeout in seconds (default: 30)')
    parser.add_argument('--delay-min', type=float, default=0.5,
                       help='Minimum delay between requests in seconds (default: 0.5)')
    parser.add_argument('--delay-max', type=float, default=2.0,
                       help='Maximum delay between requests in seconds (default: 2.0)')
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = TechnicalIndicatorsExtractor(
        headless=args.headless,
        timeout=args.timeout,
        delay_min=args.delay_min,
        delay_max=args.delay_max
    )
    
    # Check if files exist
    if not os.path.exists(args.url_file):
        logger.error(f"URL file not found: {args.url_file}")
        return 1
    
    logger.info("=== Technical Indicators Extractor ===")
    logger.info(f"URL file: {args.url_file}")
    logger.info(f"Output file: {args.output_file}")
    logger.info(f"Headless mode: {args.headless}")
    logger.info(f"Timeout: {args.timeout}s")
    logger.info(f"Delay range: {args.delay_min}-{args.delay_max}s")
    
    # Process tickers
    success = extractor.process_tickers_file(args.url_file, args.output_file)
    
    if success:
        logger.info("✅ Technical indicators extraction completed successfully!")
        return 0
    else:
        logger.error("❌ Technical indicators extraction failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())