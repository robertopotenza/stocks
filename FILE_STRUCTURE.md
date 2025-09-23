# Project File Structure

## Core Application Files

- **`main.py`** - Main entry point for the application
- **`stock_prices.py`** - Core application logic for fetching stock data
- **`technical_analysis.py`** - Technical analysis calculations (support/resistance levels)
- **`requirements.txt`** - Python dependencies
- **`tickers.xlsx`** - Excel file with stock tickers (212 stocks included)

## Configuration Files

- **`config.example.py`** - Example configuration file template
- **`Dockerfile`** - Docker container configuration for deployment
- **`Procfile`** - Process file for Railway deployment

## Documentation

- **`README.md`** - Main project documentation
- **`GETTING_STARTED.md`** - **Step-by-step setup guide (START HERE!)**
- **`TECHNICAL_ANALYSIS.md`** - Technical analysis features documentation
- **`FILE_STRUCTURE.md`** - This file

## Startup Scripts

- **`start.sh`** - Easy setup and run script for Linux/Mac
- **`start.bat`** - Easy setup and run script for Windows

## Quick File Reference

| File | Purpose | When to Use |
|------|---------|-------------|
| `GETTING_STARTED.md` | Complete setup guide | **First time setup** |
| `start.sh` / `start.bat` | Automated setup | **Easy way to run** |
| `main.py` | Run the application | **Manual execution** |
| `config.example.py` | Credential template | **Secure credential setup** |
| `tickers.xlsx` | Stock list | **Customize your stocks** |

## Getting Started Flow

1. **Read** `GETTING_STARTED.md` for complete instructions
2. **Run** `./start.sh` (Linux/Mac) or `start.bat` (Windows) for easy setup
3. **Configure** your Robinhood credentials
4. **Customize** `tickers.xlsx` with your desired stocks
5. **Execute** the application and review results

---

**🎯 TL;DR**: Run `./start.sh` and follow the prompts!