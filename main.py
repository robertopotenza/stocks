#!/usr/bin/env python3
"""
Main entry point for the Stock Data Fetcher application.

This module serves as the entry point for deployment platforms like Railpack
that expect a main.py file in the project root.
"""

from stock_prices import main

if __name__ == "__main__":
    main()