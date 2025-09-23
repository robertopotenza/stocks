#!/bin/bash

# Robinhood Stock Data Fetcher - Easy Start Script
# This script helps you set up and run the application easily

set -e  # Exit on any error

echo "🚀 Robinhood Stock Data Fetcher - Setup & Start"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# Check if Python 3 is installed
echo
print_info "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 is not installed. Please install Python 3.12+ and try again."
    exit 1
fi

# Check if pip is available
if command -v pip &> /dev/null; then
    PIP_VERSION=$(pip --version)
    print_status "pip found: $PIP_VERSION"
else
    print_error "pip is not installed. Please install pip and try again."
    exit 1
fi

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found. Are you in the correct directory?"
    exit 1
fi

# Install dependencies
echo
print_info "Installing dependencies..."
if pip install -r requirements.txt; then
    print_status "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Check if tickers.xlsx exists
echo
if [ -f "tickers.xlsx" ]; then
    print_status "Found tickers.xlsx file"
    TICKER_COUNT=$(python3 -c "import pandas as pd; print(len(pd.read_excel('tickers.xlsx')))" 2>/dev/null || echo "unknown")
    print_info "Number of tickers: $TICKER_COUNT"
else
    print_warning "tickers.xlsx not found. Creating a sample file..."
    # Create a simple sample tickers file
    python3 -c "
import pandas as pd
sample_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
df = pd.DataFrame({'Ticker': sample_tickers})
df.to_excel('tickers.xlsx', index=False)
print('Created sample tickers.xlsx with popular stocks')
"
    print_status "Created sample tickers.xlsx"
fi

# Check for credentials
echo
print_info "Checking credentials configuration..."

if [ -n "$ROBINHOOD_USERNAME" ] && [ -n "$ROBINHOOD_PASSWORD" ]; then
    print_status "Found environment variables for credentials"
    CREDS_CONFIGURED=true
elif [ -f "config.py" ]; then
    print_status "Found config.py file"
    CREDS_CONFIGURED=true
else
    print_warning "No credentials configured yet"
    CREDS_CONFIGURED=false
fi

# If credentials not configured, offer to set them up
if [ "$CREDS_CONFIGURED" = false ]; then
    echo
    print_info "Would you like to set up credentials now? (y/n)"
    read -r SETUP_CREDS
    
    if [ "$SETUP_CREDS" = "y" ] || [ "$SETUP_CREDS" = "Y" ]; then
        echo
        print_info "Choose setup method:"
        echo "1) Environment variables (recommended)"
        echo "2) Configuration file"
        echo "3) Skip for now"
        read -r SETUP_METHOD
        
        case $SETUP_METHOD in
            1)
                echo
                print_info "Enter your Robinhood credentials:"
                read -p "Username/Email: " USERNAME
                read -s -p "Password: " PASSWORD
                echo
                export ROBINHOOD_USERNAME="$USERNAME"
                export ROBINHOOD_PASSWORD="$PASSWORD"
                print_status "Environment variables set for this session"
                print_warning "To persist these, add to your shell profile (.bashrc, .zshrc, etc.)"
                CREDS_CONFIGURED=true
                ;;
            2)
                if [ ! -f "config.py" ]; then
                    cp config.example.py config.py
                fi
                print_info "Please edit config.py with your credentials, then run this script again"
                print_info "Opening config.py..."
                ${EDITOR:-nano} config.py
                ;;
            *)
                print_info "Skipping credential setup"
                ;;
        esac
    fi
fi

# Run the application
echo
if [ "$CREDS_CONFIGURED" = true ]; then
    print_info "Starting the application..."
    echo
    python3 main.py
    echo
    print_status "Application completed successfully!"
    print_info "Check the updated tickers.xlsx file for results"
else
    print_warning "Credentials not configured. The application will show a warning."
    print_info "You can:"
    echo "  1. Set environment variables: export ROBINHOOD_USERNAME=... ROBINHOOD_PASSWORD=..."
    echo "  2. Create config.py from config.example.py"
    echo "  3. Edit USERNAME/PASSWORD in stock_prices.py directly"
    echo
    print_info "Running application anyway to show the credential warning..."
    echo
    python3 main.py
fi

echo
print_info "Setup and execution completed!"
print_info "For more detailed instructions, see GETTING_STARTED.md"