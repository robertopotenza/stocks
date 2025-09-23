#!/usr/bin/env python3
"""
Demo Mode for Robinhood Stock Data Fetcher

This script demonstrates the application functionality using mock data,
so you can see how it works without needing Robinhood credentials.
"""

import pandas as pd
import random
import os
from datetime import datetime

def create_demo_tickers():
    """Create a demo tickers file"""
    demo_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']
    df = pd.DataFrame({'Ticker': demo_tickers})
    df.to_excel("demo_tickers.xlsx", index=False)
    return demo_tickers

def generate_mock_stock_data(ticker):
    """Generate realistic mock stock data"""
    # Base prices for realistic demo
    base_prices = {
        'AAPL': 180, 'GOOGL': 140, 'MSFT': 410, 'TSLA': 250,
        'AMZN': 145, 'NVDA': 850, 'META': 480, 'NFLX': 450
    }
    
    base_price = base_prices.get(ticker, 100)
    
    # Add some random variation
    current_price = round(base_price * random.uniform(0.95, 1.05), 2)
    week_52_high = round(current_price * random.uniform(1.1, 1.4), 2)
    week_52_low = round(current_price * random.uniform(0.6, 0.9), 2)
    
    # Market cap in billions
    market_cap = round(current_price * random.uniform(800, 3000), 2)
    
    # P/E ratio
    pe_ratio = round(random.uniform(15, 35), 2)
    
    # Technical analysis levels
    pivot_support_1 = round(current_price * random.uniform(0.97, 0.99), 2)
    pivot_support_2 = round(current_price * random.uniform(0.94, 0.96), 2)
    pivot_resistance_1 = round(current_price * random.uniform(1.01, 1.03), 2)
    pivot_resistance_2 = round(current_price * random.uniform(1.04, 1.06), 2)
    recent_support = round(current_price * random.uniform(0.95, 0.98), 2)
    recent_resistance = round(current_price * random.uniform(1.02, 1.05), 2)
    
    return {
        'Current_Price': current_price,
        '52_Week_High': week_52_high,
        '52_Week_Low': week_52_low,
        'Market_Cap_B': market_cap,
        'PE_Ratio': pe_ratio,
        'Pivot_Support_1': pivot_support_1,
        'Pivot_Support_2': pivot_support_2,
        'Pivot_Resistance_1': pivot_resistance_1,
        'Pivot_Resistance_2': pivot_resistance_2,
        'Recent_Support': recent_support,
        'Recent_Resistance': recent_resistance
    }

def run_demo():
    """Run the demo application"""
    print("🎭 DEMO MODE - Robinhood Stock Data Fetcher")
    print("=" * 50)
    print("This demo shows you how the application works using mock data.")
    print("No Robinhood credentials required!")
    print()
    
    # Create demo tickers
    print("📊 Creating demo ticker list...")
    tickers = create_demo_tickers()
    print(f"✅ Created demo_tickers.xlsx with {len(tickers)} stocks")
    
    # Simulate fetching data
    print(f"\n🔄 Fetching mock stock data for {len(tickers)} tickers...")
    
    results = []
    for i, ticker in enumerate(tickers, 1):
        print(f"   [{i}/{len(tickers)}] Fetching {ticker}...")
        data = generate_mock_stock_data(ticker)
        data['Ticker'] = ticker
        results.append(data)
    
    # Create results DataFrame
    df = pd.DataFrame(results)
    
    # Reorder columns to match real application
    column_order = [
        'Ticker', 'Current_Price', '52_Week_High', '52_Week_Low', 
        'Market_Cap_B', 'PE_Ratio', 'Pivot_Support_1', 'Pivot_Support_2',
        'Pivot_Resistance_1', 'Pivot_Resistance_2', 'Recent_Support', 'Recent_Resistance'
    ]
    df = df[column_order]
    
    # Save results
    output_file = "demo_results.xlsx"
    df.to_excel(output_file, index=False)
    
    print(f"\n✅ Demo complete! Results saved to '{output_file}'")
    print()
    print("📋 DEMO RESULTS SUMMARY:")
    print("-" * 30)
    
    for _, row in df.iterrows():
        print(f"📈 {row['Ticker']}: ${row['Current_Price']:.2f} "
              f"(52w: ${row['52_Week_Low']:.2f} - ${row['52_Week_High']:.2f}) "
              f"P/E: {row['PE_Ratio']}")
    
    print()
    print("📊 Technical Analysis Levels:")
    print("-" * 35)
    for _, row in df.iterrows():
        print(f"{row['Ticker']}: Support ${row['Recent_Support']:.2f} | "
              f"Resistance ${row['Recent_Resistance']:.2f}")
    
    print()
    print("🎉 This is what the real application does with actual Robinhood data!")
    print()
    print("📝 Next steps:")
    print("   • Open demo_results.xlsx to see the full data")
    print("   • Run 'python setup.py' to set up with real Robinhood credentials")
    print("   • Replace demo_tickers.xlsx with your own stock symbols")
    print()
    print("🔗 Ready for the real thing? See README.md for setup instructions")

if __name__ == "__main__":
    run_demo()