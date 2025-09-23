#!/usr/bin/env python3
"""
Easy Setup Script for Robinhood Stock Data Fetcher

This script makes it super easy to get started with the stock data fetcher.
It will guide you through the setup process step by step.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print a welcome banner"""
    print("=" * 60)
    print("🚀 ROBINHOOD STOCK DATA FETCHER - EASY SETUP")
    print("=" * 60)
    print("This script will help you set up everything you need!")
    print()

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print("❌ Error: Python 3.6+ is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible!")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages. Please run: pip install -r requirements.txt")
        return False

def setup_credentials():
    """Guide user through credential setup"""
    print("\n🔐 ROBINHOOD CREDENTIALS SETUP")
    print("-" * 40)
    print("You have 3 options for setting up your Robinhood credentials:")
    print()
    print("1. Environment Variables (Recommended - Most Secure)")
    print("2. Configuration File (Good for development)")
    print("3. Direct Script Modification (Simplest but less secure)")
    print()
    
    while True:
        choice = input("Choose an option (1-3): ").strip()
        if choice in ['1', '2', '3']:
            break
        print("Please enter 1, 2, or 3")
    
    if choice == '1':
        setup_env_variables()
    elif choice == '2':
        setup_config_file()
    elif choice == '3':
        setup_direct_modification()

def setup_env_variables():
    """Guide user through environment variable setup"""
    print("\n🌟 ENVIRONMENT VARIABLES SETUP (Recommended)")
    print("-" * 50)
    print("This is the most secure method. Your credentials won't be stored in files.")
    print()
    
    username = input("Enter your Robinhood email/username: ").strip()
    password = input("Enter your Robinhood password: ").strip()
    
    mfa_prompt = input("Do you have Multi-Factor Authentication enabled? (y/n): ").strip().lower()
    mfa_code = ""
    if mfa_prompt == 'y':
        print("\nNote: You can set MFA code later when running the app, or set it now for automation")
        mfa_code = input("Enter your current MFA code (or leave blank): ").strip()
    
    # Create a simple script to set environment variables
    env_script = f"""#!/bin/bash
# Robinhood Stock Data Fetcher Environment Variables
export ROBINHOOD_USERNAME="{username}"
export ROBINHOOD_PASSWORD="{password}"
"""
    if mfa_code:
        env_script += f'export ROBINHOOD_MFA="{mfa_code}"\n'
    
    env_script += """
# Run the stock data fetcher
python stock_prices.py
"""
    
    with open("run_with_env.sh", "w") as f:
        f.write(env_script)
    
    os.chmod("run_with_env.sh", 0o755)
    
    print("\n✅ Created 'run_with_env.sh' script!")
    print("To run the application:")
    print("   ./run_with_env.sh")
    print()
    print("Or set environment variables manually:")
    print(f'   export ROBINHOOD_USERNAME="{username}"')
    print(f'   export ROBINHOOD_PASSWORD="{password}"')
    if mfa_code:
        print(f'   export ROBINHOOD_MFA="{mfa_code}"')
    print("   python stock_prices.py")

def setup_config_file():
    """Create a configuration file"""
    print("\n📁 CONFIGURATION FILE SETUP")
    print("-" * 35)
    print("This will create a 'config.py' file with your credentials.")
    print("⚠️  Warning: Don't commit this file to version control!")
    print()
    
    username = input("Enter your Robinhood email/username: ").strip()
    password = input("Enter your Robinhood password: ").strip()
    
    config_content = f'''# Robinhood Stock Price Fetcher Configuration
# ⚠️ DO NOT COMMIT THIS FILE TO VERSION CONTROL!

# Robinhood Login Credentials
ROBINHOOD_USERNAME = "{username}"
ROBINHOOD_PASSWORD = "{password}"

# Path to Excel file containing tickers (must have 'Ticker' column)
TICKERS_FILE = "tickers.xlsx"
'''
    
    with open("config.py", "w") as f:
        f.write(config_content)
    
    print("✅ Created 'config.py' file!")
    print("To run the application:")
    print("   python stock_prices.py")

def setup_direct_modification():
    """Guide user to modify the script directly"""
    print("\n✏️  DIRECT SCRIPT MODIFICATION")
    print("-" * 35)
    print("This will modify the stock_prices.py file directly.")
    print("⚠️  Warning: Your credentials will be visible in the code!")
    print()
    
    username = input("Enter your Robinhood email/username: ").strip()
    password = input("Enter your Robinhood password: ").strip()
    
    # Read the current file
    with open("stock_prices.py", "r") as f:
        content = f.read()
    
    # Replace the credential lines
    content = content.replace('USERNAME = os.getenv("ROBINHOOD_USERNAME", "your_email")', 
                            f'USERNAME = os.getenv("ROBINHOOD_USERNAME", "{username}")')
    content = content.replace('PASSWORD = os.getenv("ROBINHOOD_PASSWORD", "your_password")', 
                            f'PASSWORD = os.getenv("ROBINHOOD_PASSWORD", "{password}")')
    
    # Write back to file
    with open("stock_prices.py", "w") as f:
        f.write(content)
    
    print("✅ Modified 'stock_prices.py' with your credentials!")
    print("To run the application:")
    print("   python stock_prices.py")

def check_tickers_file():
    """Check if tickers.xlsx exists and provide guidance"""
    print("\n📊 CHECKING TICKER FILE")
    print("-" * 25)
    
    if os.path.exists("tickers.xlsx"):
        print("✅ Found 'tickers.xlsx' file!")
        try:
            import pandas as pd
            df = pd.read_excel("tickers.xlsx")
            if 'Ticker' in df.columns:
                ticker_count = len(df)
                print(f"✅ File contains {ticker_count} tickers in 'Ticker' column")
                print("Sample tickers:", df['Ticker'].head(3).tolist())
            else:
                print("⚠️  Warning: 'tickers.xlsx' doesn't have a 'Ticker' column")
                print("   Please add a 'Ticker' column with stock symbols (e.g., AAPL, GOOGL)")
        except Exception as e:
            print(f"⚠️  Warning: Could not read tickers.xlsx: {e}")
    else:
        print("📝 'tickers.xlsx' not found. Creating a sample file...")
        create_sample_tickers_file()

def create_sample_tickers_file():
    """Create a sample tickers file"""
    try:
        import pandas as pd
        sample_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        df = pd.DataFrame({'Ticker': sample_tickers})
        df.to_excel("tickers.xlsx", index=False)
        print("✅ Created sample 'tickers.xlsx' with popular stocks!")
        print("   Edit this file to add your own stock symbols.")
    except Exception as e:
        print(f"❌ Could not create sample file: {e}")

def print_final_instructions():
    """Print final instructions"""
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("Your Robinhood Stock Data Fetcher is ready to use!")
    print()
    print("📋 Quick Start:")
    if os.path.exists("run_with_env.sh"):
        print("   ./run_with_env.sh")
    else:
        print("   python stock_prices.py")
    print()
    print("📚 What the app does:")
    print("   • Logs into your Robinhood account")
    print("   • Reads stock symbols from tickers.xlsx")
    print("   • Fetches comprehensive stock data (price, market cap, P/E, etc.)")
    print("   • Calculates technical analysis levels")
    print("   • Writes results back to tickers.xlsx")
    print()
    print("🚀 For deployment options see README.md")
    print("   • Docker deployment")
    print("   • Railway cloud deployment")
    print()
    print("💡 Need help? Check the troubleshooting section in README.md")

def main():
    """Main setup function"""
    print_banner()
    
    if not check_python_version():
        return
    
    if not install_dependencies():
        return
    
    setup_credentials()
    check_tickers_file()
    print_final_instructions()

if __name__ == "__main__":
    main()