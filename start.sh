#!/bin/bash

# Robinhood Stock Data Fetcher - Easy Start Script
# This is the simplest way to get started!

echo "🚀 Robinhood Stock Data Fetcher - Easy Start"
echo "=============================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python is not installed. Please install Python 3.6+ first."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "✅ Found Python: $($PYTHON_CMD --version)"

# Check if this is first time setup
if [ ! -f "setup_complete.flag" ]; then
    echo ""
    echo "👋 First time setup detected!"
    echo "Running easy setup wizard..."
    echo ""
    $PYTHON_CMD setup.py
    
    # Check if setup was successful
    if [ $? -eq 0 ]; then
        touch setup_complete.flag
        echo ""
        echo "🎉 Setup complete! Starting the application..."
        echo ""
    else
        echo "❌ Setup failed. Please check the errors above."
        exit 1
    fi
fi

# Run the application
$PYTHON_CMD run.py