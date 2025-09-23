@echo off
REM Robinhood Stock Data Fetcher - Easy Start Script for Windows
REM This script helps you set up and run the application easily

echo 🚀 Robinhood Stock Data Fetcher - Setup ^& Start
echo ================================================

REM Check if Python is installed
echo.
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.12+ and try again.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python found: %PYTHON_VERSION%

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed. Please install pip and try again.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('pip --version') do set PIP_VERSION=%%i
echo ✅ pip found: %PIP_VERSION%

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo ❌ requirements.txt not found. Are you in the correct directory?
    pause
    exit /b 1
)

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed successfully

REM Check if tickers.xlsx exists
echo.
if exist "tickers.xlsx" (
    echo ✅ Found tickers.xlsx file
) else (
    echo ⚠️ tickers.xlsx not found. Creating a sample file...
    python -c "import pandas as pd; sample_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']; df = pd.DataFrame({'Ticker': sample_tickers}); df.to_excel('tickers.xlsx', index=False); print('Created sample tickers.xlsx')"
    echo ✅ Created sample tickers.xlsx
)

REM Check for credentials
echo.
echo Checking credentials configuration...

if defined ROBINHOOD_USERNAME (
    if defined ROBINHOOD_PASSWORD (
        echo ✅ Found environment variables for credentials
        set CREDS_CONFIGURED=true
        goto run_app
    )
)

if exist "config.py" (
    echo ✅ Found config.py file
    set CREDS_CONFIGURED=true
    goto run_app
)

echo ⚠️ No credentials configured yet
echo.
echo To configure credentials, you can:
echo 1. Set environment variables:
echo    set ROBINHOOD_USERNAME=your_email@example.com
echo    set ROBINHOOD_PASSWORD=your_password
echo.
echo 2. Copy config.example.py to config.py and edit it
echo.
echo 3. Edit USERNAME/PASSWORD directly in stock_prices.py
echo.
echo The application will show a warning about missing credentials.

:run_app
REM Run the application
echo.
echo Starting the application...
echo.
python main.py

echo.
echo ✅ Application completed!
echo Check the updated tickers.xlsx file for results
echo.
echo For more detailed instructions, see GETTING_STARTED.md
echo.
pause