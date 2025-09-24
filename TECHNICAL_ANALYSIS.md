# Technical Analysis Features

## Overview
The enhanced Stock Data Fetcher now includes comprehensive technical analysis capabilities to extract Support and Resistance levels for each ticker. This functionality uses historical price data from the Robinhood API to calculate key technical levels that traders use for decision-making.

## New Features Added

### 1. Pivot Point Analysis
**Classical pivot point calculations** using the most recent trading day's data:

- **Pivot Point**: `(High + Low + Close) / 3`
- **Support Level 1**: `(2 × Pivot Point) - High`
- **Support Level 2**: `Pivot Point - (High - Low)`
- **Resistance Level 1**: `(2 × Pivot Point) - Low`
- **Resistance Level 2**: `Pivot Point + (High - Low)`

### 2. Recent Price Action Analysis
**20-day lookback analysis** to identify:
- Recent support levels (lowest lows in the period)
- Recent resistance levels (highest highs in the period)
- Secondary support/resistance levels for confirmation

### 3. Historical Data Integration
- **Data Source**: Robinhood API historical stock data
- **Time Period**: 3 months of daily OHLC (Open, High, Low, Close) data
- **Interval**: Daily price data for accurate calculations
- **Error Handling**: Graceful handling of missing or insufficient data

## Excel Output Enhancements

The following **6 new columns** have been added to the Excel output:

| Column Name | Description |
|-------------|-------------|
| `Pivot_Support_1` | Primary pivot-based support level |
| `Pivot_Support_2` | Secondary pivot-based support level |
| `Pivot_Resistance_1` | Primary pivot-based resistance level |
| `Pivot_Resistance_2` | Secondary pivot-based resistance level |
| `Recent_Support` | Support level from 20-day price action |
| `Recent_Resistance` | Resistance level from 20-day price action |

## Usage Example

### Input
```bash
python stock_prices.py
```

### Sample Output
```
📈 Fetching stock data for 8 tickers...
  1/8 AAPL: Calculating technical levels...
  1/8 AAPL: $191.50 | Sup: 189.25 | Res: 194.15
  2/8 GOOGL: Calculating technical levels...
  2/8 GOOGL: $2845.30 | Sup: 2781.45 | Res: 2909.15

===============================================================================
         STOCK DATA SUMMARY
===============================================================================
    AAPL: $    191.50 | 52w: $  199.62-$  124.17 | Cap: 3000000000000 | P/E:  29.20
          Pivot S/R: $189.25-$194.15 | Recent S/R: $187.60-$193.80
   GOOGL: $   2845.30 | 52w: $ 3030.93-$ 2193.62 | Cap: 1850000000000 | P/E:  24.80
          Pivot S/R: $2781.45-$2909.15 | Recent S/R: $2765.30-$2890.75
===============================================================================
```

## Technical Implementation

### New Files
- **`technical_analysis.py`**: Core technical analysis module with calculation functions
- **Enhanced `stock_prices.py`**: Integrated technical analysis into main workflow

### Key Functions
- `get_historical_data()`: Fetches historical OHLC data from Robinhood
- `calculate_pivot_points()`: Computes pivot-based support/resistance levels
- `find_recent_support_resistance()`: Analyzes recent price action for S/R levels
- `calculate_technical_levels()`: Main function combining all technical analysis

### Error Handling
- Handles insufficient historical data gracefully
- Returns 'N/A' for missing or invalid calculations
- Continues processing other tickers if one fails
- Comprehensive error logging for debugging

## Trading Applications

### Support Levels (Buy Zones)
- **Pivot Support 1 & 2**: Classical support levels for potential buying opportunities
- **Recent Support**: Price levels where recent buying interest emerged

### Resistance Levels (Sell Zones)  
- **Pivot Resistance 1 & 2**: Classical resistance levels for potential selling opportunities
- **Recent Resistance**: Price levels where recent selling pressure appeared

### Risk Management
- Use support levels as stop-loss placement guides
- Use resistance levels as profit-taking targets
- Multiple levels provide confirmation and backup targets

## Data Requirements
- **Minimum**: 5 days of historical data for basic calculations
- **Optimal**: 60+ days (3 months) for robust analysis
- **Fallback**: Returns 'N/A' when insufficient data is available

## Future Enhancements
Potential additions for future versions:
- Volume-weighted support/resistance levels
- Fibonacci retracement levels
- Moving average support/resistance
- Bollinger Bands integration
- RSI divergence analysis