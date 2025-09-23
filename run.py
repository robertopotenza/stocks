#!/usr/bin/env python3
"""
Easy Run Script for Robinhood Stock Data Fetcher

This script provides the easiest way to run the stock data fetcher with 
helpful guidance and error handling.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print a welcome banner"""
    print("=" * 60)
    print("🚀 ROBINHOOD STOCK DATA FETCHER")
    print("=" * 60)

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import robin_stocks
        import pandas
        import openpyxl
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\n📦 Installing required packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Packages installed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages.")
            print("Please run: pip install -r requirements.txt")
            return False

def check_credentials():
    """Check if credentials are configured"""
    # Check environment variables
    username = os.getenv("ROBINHOOD_USERNAME")
    password = os.getenv("ROBINHOOD_PASSWORD")
    
    if username and password and username != "your_email" and password != "your_password":
        print("✅ Credentials found in environment variables")
        return True
    
    # Check config file
    if os.path.exists("config.py"):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", "config.py")
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
            
            if (hasattr(config, 'ROBINHOOD_USERNAME') and 
                hasattr(config, 'ROBINHOOD_PASSWORD') and
                config.ROBINHOOD_USERNAME != "your_email" and
                config.ROBINHOOD_PASSWORD != "your_password"):
                print("✅ Credentials found in config.py")
                return True
        except Exception:
            pass
    
    # Check if script was modified
    try:
        with open("stock_prices.py", "r") as f:
            content = f.read()
            if ('USERNAME = os.getenv("ROBINHOOD_USERNAME", "your_email")' not in content or 
                'PASSWORD = os.getenv("ROBINHOOD_PASSWORD", "your_password")' not in content):
                print("✅ Credentials found in stock_prices.py")
                return True
    except Exception:
        pass
    
    return False

def check_tickers_file():
    """Check if tickers file exists"""
    if os.path.exists("tickers.xlsx"):
        print("✅ Found tickers.xlsx file")
        return True
    else:
        print("⚠️  Warning: tickers.xlsx not found")
        return False

def provide_setup_guidance():
    """Provide guidance on how to set up the application"""
    print("\n❌ SETUP REQUIRED")
    print("-" * 20)
    print("It looks like this is your first time running the app!")
    print()
    print("🛠️  To get started, you have two options:")
    print()
    print("1. 🌟 EASY SETUP (Recommended):")
    print("   python setup.py")
    print("   (This will guide you through everything step-by-step)")
    print()
    print("2. ⚡ QUICK SETUP:")
    print("   Set environment variables and run:")
    print("   export ROBINHOOD_USERNAME=your_email@example.com")
    print("   export ROBINHOOD_PASSWORD=your_password")
    print("   python stock_prices.py")
    print()
    print("🔗 For more options, see README.md")

def provide_missing_tickers_guidance():
    """Provide guidance when tickers file is missing"""
    print("\n📊 MISSING TICKERS FILE")
    print("-" * 25)
    print("You need a 'tickers.xlsx' file with stock symbols to fetch data for.")
    print()
    print("📝 Quick fix:")
    print("   python setup.py")
    print("   (This will create a sample tickers.xlsx file)")
    print()
    print("Or manually create an Excel file named 'tickers.xlsx' with:")
    print("   • A column named 'Ticker'")
    print("   • Stock symbols like: AAPL, GOOGL, MSFT, TSLA")

def run_application():
    """Run the main application"""
    print("\n🚀 Starting Stock Data Fetcher...")
    print("-" * 35)
    
    try:
        from stock_prices import main
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error running application: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   • Check your internet connection")
        print("   • Verify your Robinhood credentials")
        print("   • Make sure tickers.xlsx has valid stock symbols")
        print("   • See README.md for more help")

def main():
    """Main function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check credentials
    credentials_ok = check_credentials()
    tickers_ok = check_tickers_file()
    
    if not credentials_ok:
        provide_setup_guidance()
        return
    
    if not tickers_ok:
        provide_missing_tickers_guidance()
        return
    
    # Everything looks good, run the application
    run_application()

if __name__ == "__main__":
    main()