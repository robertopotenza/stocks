#!/usr/bin/env python3
"""
Production Debugging Script for Technical Indicators Extractor

This script provides comprehensive debugging for production environments
to identify why the extractor is falling back to mock data.

Usage:
    python production_debug.py [--full-test]
    
Environment:
    Run this inside the production container to debug connectivity issues.
"""

import os
import sys
import socket
import subprocess
import time
import urllib.parse
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ProductionDebugger:
    """Comprehensive debugging for production environment issues."""
    
    def __init__(self):
        self.test_urls = [
            'https://www.investing.com/equities/aia-group-ltd-technical',
            'https://www.investing.com/equities/apple-computer-inc-technical',
            'https://www.google.com',
            'https://httpbin.org/get'
        ]
        self.dns_servers = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
        self.results = {}
    
    def print_header(self, title: str):
        """Print formatted section header."""
        print("\n" + "=" * 80)
        print(f"🔍 {title}")
        print("=" * 80)
    
    def print_section(self, title: str):
        """Print formatted subsection header."""
        print(f"\n📋 {title}")
        print("-" * 60)
    
    def check_environment_variables(self) -> Dict[str, Any]:
        """Check relevant environment variables."""
        self.print_section("Environment Variables Check")
        
        env_vars = {
            'HTTP_PROXY': os.getenv('HTTP_PROXY'),
            'HTTPS_PROXY': os.getenv('HTTPS_PROXY'), 
            'http_proxy': os.getenv('http_proxy'),
            'https_proxy': os.getenv('https_proxy'),
            'NO_PROXY': os.getenv('NO_PROXY'),
            'DNS_SERVER': os.getenv('DNS_SERVER'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL'),
            'PATH': os.getenv('PATH'),
            'PYTHONPATH': os.getenv('PYTHONPATH')
        }
        
        results = {}
        for var, value in env_vars.items():
            if value:
                print(f"✅ {var}={value}")
                results[var] = value
            else:
                print(f"❌ {var}=<not set>")
                results[var] = None
        
        # Check container-specific variables
        container_vars = ['HOSTNAME', 'USER', 'HOME', 'PWD']
        for var in container_vars:
            value = os.getenv(var)
            if value:
                print(f"ℹ️  {var}={value}")
        
        self.results['environment'] = results
        return results
    
    def check_dns_resolution(self) -> Dict[str, Any]:
        """Test DNS resolution for target domains."""
        self.print_section("DNS Resolution Check")
        
        domains = ['www.investing.com', 'google.com', 'github.com']
        results = {}
        
        for domain in domains:
            try:
                start_time = time.time()
                ip_address = socket.gethostbyname(domain)
                resolve_time = time.time() - start_time
                print(f"✅ {domain} → {ip_address} ({resolve_time:.3f}s)")
                results[domain] = {'status': 'success', 'ip': ip_address, 'time': resolve_time}
            except socket.gaierror as e:
                print(f"❌ {domain} → DNS Error: {e}")
                results[domain] = {'status': 'error', 'error': str(e)}
            except Exception as e:
                print(f"❌ {domain} → Unexpected Error: {e}")
                results[domain] = {'status': 'error', 'error': str(e)}
        
        self.results['dns'] = results
        return results
    
    def check_network_connectivity(self) -> Dict[str, Any]:
        """Test basic network connectivity."""
        self.print_section("Network Connectivity Check")
        
        results = {}
        
        # Test ping to known servers
        ping_targets = ['8.8.8.8', '1.1.1.1', 'google.com']
        
        for target in ping_targets:
            try:
                result = subprocess.run(
                    ['ping', '-c', '3', '-W', '5', target],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print(f"✅ Ping {target}: Success")
                    results[f'ping_{target}'] = {'status': 'success', 'output': result.stdout}
                else:
                    print(f"❌ Ping {target}: Failed")
                    results[f'ping_{target}'] = {'status': 'failed', 'error': result.stderr}
            except subprocess.TimeoutExpired:
                print(f"⏰ Ping {target}: Timeout")
                results[f'ping_{target}'] = {'status': 'timeout'}
            except FileNotFoundError:
                print(f"⚠️  Ping command not available")
                break
            except Exception as e:
                print(f"❌ Ping {target}: Error - {e}")
                results[f'ping_{target}'] = {'status': 'error', 'error': str(e)}
        
        self.results['connectivity'] = results
        return results
    
    def check_http_requests(self) -> Dict[str, Any]:
        """Test HTTP requests to target URLs."""
        self.print_section("HTTP Requests Check")
        
        results = {}
        
        try:
            import requests
            from fake_useragent import UserAgent
            
            ua = UserAgent()
            headers = {
                'User-Agent': ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            for url in self.test_urls:
                try:
                    start_time = time.time()
                    response = requests.get(url, headers=headers, timeout=10)
                    request_time = time.time() - start_time
                    
                    print(f"✅ {url}")
                    print(f"   Status: {response.status_code}")
                    print(f"   Time: {request_time:.3f}s")
                    print(f"   Size: {len(response.content)} bytes")
                    
                    results[url] = {
                        'status': 'success',
                        'status_code': response.status_code,
                        'time': request_time,
                        'size': len(response.content),
                        'headers': dict(response.headers)
                    }
                    
                except requests.exceptions.RequestException as e:
                    print(f"❌ {url}: {type(e).__name__}: {e}")
                    results[url] = {'status': 'error', 'error': str(e), 'error_type': type(e).__name__}
                except Exception as e:
                    print(f"❌ {url}: Unexpected Error: {e}")
                    results[url] = {'status': 'error', 'error': str(e)}
        
        except ImportError as e:
            print(f"❌ Required modules not available: {e}")
            results['import_error'] = str(e)
        
        self.results['http_requests'] = results
        return results
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check Python dependencies and their versions."""
        self.print_section("Dependencies Check")
        
        required_packages = [
            'requests', 'beautifulsoup4', 'selenium', 'fake_useragent',
            'pandas', 'openpyxl', 'lxml'
        ]
        
        results = {}
        
        for package in required_packages:
            try:
                module = __import__(package.replace('-', '_'))
                version = getattr(module, '__version__', 'unknown')
                print(f"✅ {package}: {version}")
                results[package] = {'status': 'available', 'version': version}
            except ImportError:
                print(f"❌ {package}: Not installed")
                results[package] = {'status': 'missing'}
            except Exception as e:
                print(f"⚠️  {package}: Error - {e}")
                results[package] = {'status': 'error', 'error': str(e)}
        
        self.results['dependencies'] = results
        return results
    
    def check_selenium_setup(self) -> Dict[str, Any]:
        """Check Selenium and Chrome driver availability."""
        self.print_section("Selenium & Chrome Driver Check")
        
        results = {}
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            print("✅ Selenium module available")
            results['selenium_import'] = 'success'
            
            # Check Chrome availability
            chrome_paths = ['/usr/bin/google-chrome', '/usr/bin/chromium-browser', '/usr/bin/chromium']
            chrome_found = False
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    print(f"✅ Chrome found at: {chrome_path}")
                    results['chrome_path'] = chrome_path
                    chrome_found = True
                    break
            
            if not chrome_found:
                print("❌ Chrome browser not found")
                results['chrome_path'] = None
            
            # Try to create a headless Chrome driver
            try:
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                
                driver = webdriver.Chrome(options=options)
                print("✅ Chrome WebDriver creation successful")
                driver.quit()
                results['webdriver'] = 'success'
                
            except Exception as e:
                print(f"❌ Chrome WebDriver failed: {e}")
                results['webdriver'] = {'status': 'error', 'error': str(e)}
        
        except ImportError:
            print("❌ Selenium not available")
            results['selenium_import'] = 'missing'
        except Exception as e:
            print(f"❌ Selenium error: {e}")
            results['selenium_import'] = {'status': 'error', 'error': str(e)}
        
        self.results['selenium'] = results
        return results
    
    def check_file_permissions(self) -> Dict[str, Any]:
        """Check file system permissions."""
        self.print_section("File Permissions Check")
        
        results = {}
        test_files = ['URL.xlsx', 'tickers.xlsx', '/tmp/test_write.txt']
        
        for file_path in test_files:
            try:
                if file_path.startswith('/tmp/'):
                    # Test write permission
                    with open(file_path, 'w') as f:
                        f.write("test")
                    os.remove(file_path)
                    print(f"✅ Write permission OK: {file_path}")
                    results[file_path] = 'writable'
                else:
                    # Check existing files
                    if os.path.exists(file_path):
                        if os.access(file_path, os.R_OK):
                            print(f"✅ Read permission OK: {file_path}")
                            results[file_path] = 'readable'
                        else:
                            print(f"❌ No read permission: {file_path}")
                            results[file_path] = 'not_readable'
                    else:
                        print(f"⚠️  File not found: {file_path}")
                        results[file_path] = 'not_found'
            except Exception as e:
                print(f"❌ Permission error {file_path}: {e}")
                results[file_path] = {'status': 'error', 'error': str(e)}
        
        self.results['permissions'] = results
        return results
    
    def run_extractor_test(self) -> Dict[str, Any]:
        """Run a controlled test of the extractor."""
        self.print_section("Extractor Test Run")
        
        results = {}
        
        try:
            # Set debug logging
            os.environ['LOG_LEVEL'] = 'DEBUG'
            
            from technical_indicators_extractor import TechnicalIndicatorsExtractor
            
            # Create extractor instance
            extractor = TechnicalIndicatorsExtractor(headless=True, timeout=10)
            
            # Test single URL
            test_ticker = "TEST"
            test_url = "https://www.investing.com/equities/apple-computer-inc-technical"
            
            print(f"🔄 Testing extraction for {test_ticker} from {test_url}")
            
            start_time = time.time()
            result = extractor.extract_indicators_for_ticker(test_ticker, test_url)
            test_time = time.time() - start_time
            
            print(f"✅ Extraction completed in {test_time:.3f}s")
            print(f"   Data Quality: {result.get('data_quality', 'unknown')}")
            print(f"   Notes: {result.get('notes', 'none')}")
            
            results = {
                'status': 'success',
                'test_time': test_time,
                'data_quality': result.get('data_quality'),
                'notes': result.get('notes'),
                'indicators_count': len([k for k, v in result.items() if k.startswith(('Woodies_', 'EMA', 'SMA', 'RSI', 'MACD', 'Bollinger', 'Volume', 'ADX', 'ATR'))])
            }
            
        except Exception as e:
            print(f"❌ Extractor test failed: {e}")
            results = {'status': 'error', 'error': str(e)}
        
        self.results['extractor_test'] = results
        return results
    
    def generate_summary(self):
        """Generate debugging summary with recommendations."""
        self.print_header("DEBUGGING SUMMARY & RECOMMENDATIONS")
        
        issues_found = []
        recommendations = []
        
        # Analyze DNS issues
        if 'dns' in self.results:
            failed_dns = [domain for domain, result in self.results['dns'].items() 
                         if result.get('status') == 'error']
            if failed_dns:
                issues_found.append(f"DNS Resolution Failed: {', '.join(failed_dns)}")
                recommendations.append("Configure DNS servers or add to /etc/hosts")
        
        # Analyze connectivity issues
        if 'connectivity' in self.results:
            failed_pings = [target for target, result in self.results['connectivity'].items() 
                          if result.get('status') != 'success']
            if failed_pings:
                issues_found.append(f"Network Connectivity Issues: {', '.join(failed_pings)}")
                recommendations.append("Check firewall rules and network policies")
        
        # Analyze HTTP request issues
        if 'http_requests' in self.results:
            failed_requests = [url for url, result in self.results['http_requests'].items() 
                             if result.get('status') == 'error']
            if failed_requests:
                issues_found.append(f"HTTP Request Failures: {len(failed_requests)} URLs failed")
                recommendations.append("Check proxy settings and SSL certificates")
        
        # Analyze dependency issues
        if 'dependencies' in self.results:
            missing_deps = [pkg for pkg, result in self.results['dependencies'].items() 
                           if result.get('status') == 'missing']
            if missing_deps:
                issues_found.append(f"Missing Dependencies: {', '.join(missing_deps)}")
                recommendations.append("Install missing Python packages")
        
        # Analyze environment variables
        if 'environment' in self.results:
            if not any(self.results['environment'].get(var) for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']):
                if issues_found:  # Only suggest proxy if other network issues exist
                    recommendations.append("Configure proxy settings if behind corporate firewall")
        
        print("\n🔍 ISSUES IDENTIFIED:")
        if issues_found:
            for i, issue in enumerate(issues_found, 1):
                print(f"{i}. {issue}")
        else:
            print("   No major issues detected!")
        
        print("\n💡 RECOMMENDATIONS:")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("   System appears to be configured correctly.")
        
        # Specific DNS fix for investing.com
        if 'www.investing.com' in str(issues_found):
            print("\n🎯 SPECIFIC FIX FOR INVESTING.COM:")
            print("   Add to /etc/hosts: 5.254.205.57 www.investing.com investing.com")
            print("   Or configure DNS server: export DNS_SERVER=8.8.8.8")
            print("   Or use proxy: export HTTPS_PROXY=http://proxy:port")
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"   Environment Variables: {len([v for v in self.results.get('environment', {}).values() if v])}/8 configured")
        print(f"   DNS Resolution: {len([r for r in self.results.get('dns', {}).values() if r.get('status') == 'success'])}/{len(self.results.get('dns', {}))} successful")
        print(f"   Dependencies: {len([r for r in self.results.get('dependencies', {}).values() if r.get('status') == 'available'])}/{len(self.results.get('dependencies', {}))} available")
        print(f"   Extractor Test: {self.results.get('extractor_test', {}).get('status', 'not_run')}")
    
    def run_full_debug(self):
        """Run comprehensive debugging suite."""
        self.print_header("PRODUCTION ENVIRONMENT DEBUG")
        print("This script will diagnose why the technical indicators extractor")
        print("is falling back to mock data in production.")
        
        # Run all diagnostic checks
        self.check_environment_variables()
        self.check_dns_resolution()
        self.check_network_connectivity()
        self.check_dependencies()
        self.check_selenium_setup()
        self.check_file_permissions()
        self.check_http_requests()
        self.run_extractor_test()
        
        # Generate summary
        self.generate_summary()
        
        return self.results

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Production debugging for technical indicators extractor')
    parser.add_argument('--full-test', action='store_true', help='Run full diagnostic suite')
    parser.add_argument('--quick', action='store_true', help='Run quick diagnostic only')
    
    args = parser.parse_args()
    
    debugger = ProductionDebugger()
    
    if args.quick:
        debugger.check_dns_resolution()
        debugger.check_http_requests()
    else:
        debugger.run_full_debug()

if __name__ == "__main__":
    main()