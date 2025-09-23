#!/usr/bin/env python3
"""
Test script for financial metrics calculations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_prices import calculate_financial_metrics

def test_financial_metrics():
    """Test the calculate_financial_metrics function with sample data"""
    
    # Test case 1: Complete data
    stock_data_1 = {
        'Price': 150.0,
        '52w_High': 200.0,
        '52w_Low': 100.0,
        'PE_Ratio': 25.0,
        'Recent_Support': 145.0,
        'Recent_Resistance': 160.0,
        'Pivot_Support_1': 140.0,
        'Pivot_Resistance_1': 155.0
    }
    
    print("Test Case 1: Complete data")
    print("Input:", stock_data_1)
    calculate_financial_metrics(stock_data_1)
    print("Output:")
    for key, value in stock_data_1.items():
        if key not in ['Price', '52w_High', '52w_Low', 'PE_Ratio', 'Recent_Support', 'Recent_Resistance', 'Pivot_Support_1', 'Pivot_Resistance_1']:
            print(f"  {key}: {value}")
    print()
    
    # Test case 2: Undervalued stock (PE < 20)
    stock_data_2 = {
        'Price': 100.0,
        '52w_High': 120.0,
        '52w_Low': 80.0,
        'PE_Ratio': 15.0,
        'Recent_Support': 95.0,
        'Recent_Resistance': 110.0,
        'Pivot_Support_1': 90.0,
        'Pivot_Resistance_1': 105.0
    }
    
    print("Test Case 2: Undervalued stock (PE < 20)")
    print("Input:", stock_data_2)
    calculate_financial_metrics(stock_data_2)
    print("Output:")
    for key, value in stock_data_2.items():
        if key not in ['Price', '52w_High', '52w_Low', 'PE_Ratio', 'Recent_Support', 'Recent_Resistance', 'Pivot_Support_1', 'Pivot_Resistance_1']:
            print(f"  {key}: {value}")
    print()
    
    # Test case 3: Near 52-week high
    stock_data_3 = {
        'Price': 195.0,
        '52w_High': 200.0,
        '52w_Low': 100.0,
        'PE_Ratio': 35.0,
        'Recent_Support': 190.0,
        'Recent_Resistance': 200.0,
        'Pivot_Support_1': 185.0,
        'Pivot_Resistance_1': 198.0
    }
    
    print("Test Case 3: Near 52-week high")
    print("Input:", stock_data_3)
    calculate_financial_metrics(stock_data_3)
    print("Output:")
    for key, value in stock_data_3.items():
        if key not in ['Price', '52w_High', '52w_Low', 'PE_Ratio', 'Recent_Support', 'Recent_Resistance', 'Pivot_Support_1', 'Pivot_Resistance_1']:
            print(f"  {key}: {value}")
    print()
    
    # Test case 4: Missing data (should handle gracefully)
    stock_data_4 = {
        'Price': 'N/A',
        '52w_High': 200.0,
        '52w_Low': 100.0,
        'PE_Ratio': 25.0,
        'Recent_Support': 'N/A',
        'Recent_Resistance': 'N/A',
        'Pivot_Support_1': 'N/A',
        'Pivot_Resistance_1': 'N/A'
    }
    
    print("Test Case 4: Missing price data")
    print("Input:", stock_data_4)
    calculate_financial_metrics(stock_data_4)
    print("Output:")
    for key, value in stock_data_4.items():
        if key not in ['Price', '52w_High', '52w_Low', 'PE_Ratio', 'Recent_Support', 'Recent_Resistance', 'Pivot_Support_1', 'Pivot_Resistance_1']:
            print(f"  {key}: {value}")
    print()
    
    # Test case 5: High risk/reward ratio (should be Favorable)
    stock_data_5 = {
        'Price': 100.0,
        '52w_High': 120.0,
        '52w_Low': 80.0,
        'PE_Ratio': 15.0,
        'Recent_Support': 95.0,
        'Recent_Resistance': 115.0,  # Higher resistance for better R/R
        'Pivot_Support_1': 90.0,
        'Pivot_Resistance_1': 105.0
    }
    
    print("Test Case 5: High risk/reward ratio")
    print("Input:", stock_data_5)
    calculate_financial_metrics(stock_data_5)
    print("Output:")
    for key, value in stock_data_5.items():
        if key not in ['Price', '52w_High', '52w_Low', 'PE_Ratio', 'Recent_Support', 'Recent_Resistance', 'Pivot_Support_1', 'Pivot_Resistance_1']:
            print(f"  {key}: {value}")
    print()

if __name__ == "__main__":
    test_financial_metrics()