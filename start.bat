@echo off
REM Robinhood Stock Data Fetcher - Easy Start Script for Windows
REM This is the simplest way to get started on Windows!

echo 🚀 Robinhood Stock Data Fetcher - Easy Start (Windows)
echo ===============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Python is not installed. Please install Python 3.6+ first.
        echo    Download from: https://python.org/downloads
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

for /f "tokens=*" %%i in ('%PYTHON_CMD% --version') do echo ✅ Found %%i

REM Check if this is first time setup
if not exist "setup_complete.flag" (
    echo.
    echo 👋 First time setup detected!
    echo Running easy setup wizard...
    echo.
    %PYTHON_CMD% setup.py
    
    if %errorlevel% equ 0 (
        echo. > setup_complete.flag
        echo.
        echo 🎉 Setup complete! Starting the application...
        echo.
    ) else (
        echo ❌ Setup failed. Please check the errors above.
        pause
        exit /b 1
    )
)

REM Run the application
%PYTHON_CMD% run.py

echo.
echo Press any key to exit...
pause >nul