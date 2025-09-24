#!/usr/bin/env python3
"""
Production Health Check for Technical Indicators Extractor

Quick health check to verify the extractor can access required resources.
Returns exit code 0 if healthy, 1 if issues detected.

Usage:
    python health_check.py
    
Environment:
    Designed to run in production containers for monitoring.
"""

import sys
import socket
import time
from typing import Dict, Any

def check_dns_resolution() -> bool:
    """Quick DNS resolution check for critical domains."""
    critical_domains = ['www.investing.com', 'investing.com']
    
    for domain in critical_domains:
        try:
            socket.gethostbyname(domain)
            print(f"✅ DNS OK: {domain}")
            return True
        except socket.gaierror:
            print(f"❌ DNS FAILED: {domain}")
    
    return False

def check_http_connectivity() -> bool:
    """Quick HTTP connectivity check."""
    try:
        import requests
        
        # Quick test to a reliable endpoint
        test_url = "https://www.investing.com/equities/apple-computer-inc-technical"
        
        response = requests.head(test_url, timeout=5)
        if response.status_code in [200, 301, 302]:
            print(f"✅ HTTP OK: {response.status_code}")
            return True
        else:
            print(f"⚠️  HTTP WARNING: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ HTTP FAILED: {e}")
        return False

def check_dependencies() -> bool:
    """Check critical dependencies are available."""
    required_modules = ['requests', 'bs4', 'pandas']
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ DEP OK: {module}")
        except ImportError:
            print(f"❌ DEP MISSING: {module}")
            return False
    
    return True

def main():
    """Main health check function."""
    print("🏥 Technical Indicators Extractor - Health Check")
    print("=" * 50)
    
    start_time = time.time()
    
    # Run checks
    dns_ok = check_dns_resolution()
    http_ok = check_http_connectivity()
    deps_ok = check_dependencies()
    
    # Overall health
    healthy = dns_ok and http_ok and deps_ok
    
    duration = time.time() - start_time
    
    print("-" * 50)
    if healthy:
        print(f"✅ HEALTHY - All systems operational ({duration:.1f}s)")
        sys.exit(0)
    else:
        print(f"❌ UNHEALTHY - Issues detected ({duration:.1f}s)")
        print()
        print("🔧 Quick fixes:")
        if not dns_ok:
            print("   DNS: Add '5.254.205.57 www.investing.com' to /etc/hosts")
        if not http_ok:
            print("   HTTP: Check proxy/firewall settings")
        if not deps_ok:
            print("   DEPS: Run 'pip install -r requirements.txt'")
        print()
        print("🔍 For detailed diagnosis: python production_debug.py")
        sys.exit(1)

if __name__ == "__main__":
    main()