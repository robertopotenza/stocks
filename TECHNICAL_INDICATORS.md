# Technical Indicators Extraction Module

This module provides comprehensive technical indicators extraction from web pages, specifically designed to work with investing.com URLs. It extracts key technical analysis indicators and updates the Excel files with the results.

## Features

### Extracted Indicators

The module extracts the following technical indicators:

#### Woodie's Pivot Points
- **Pivot**: Main pivot point level
- **S1**: First support level
- **S2**: Second support level  
- **R1**: First resistance level
- **R2**: Second resistance level

#### Moving Averages
- **EMA20**: 20-period Exponential Moving Average
- **SMA50**: 50-period Simple Moving Average

#### Momentum Indicators
- **RSI(14)**: 14-period Relative Strength Index
- **ADX(14)**: 14-period Average Directional Index
- **ATR(14)**: 14-period Average True Range

#### MACD (Moving Average Convergence Divergence)
- **MACD_value**: MACD line value
- **MACD_signal**: Signal line value
- **MACD_histogram**: Histogram value

#### Bollinger Bands
- **Bollinger_upper**: Upper band
- **Bollinger_middle**: Middle band (SMA)
- **Bollinger_lower**: Lower band

#### Volume
- **Volume_daily**: Daily trading volume

### Data Quality and Reliability

The module implements multiple extraction strategies for reliability:

1. **Primary Method**: HTTP requests with BeautifulSoup (fast)
2. **Fallback Method**: Selenium WebDriver (for JavaScript-heavy pages)
3. **Mock Data**: Consistent mock data when network is unavailable

#### Data Quality Levels
- **good**: 3+ indicators successfully extracted
- **partial**: 1-2 indicators successfully extracted
- **mock**: Mock data used (network unavailable)
- **fallback**: No data extracted

## Usage

### Command Line Interface

```bash
# Basic usage with defaults
python run_technical_indicators.py

# Run with custom parameters
python run_technical_indicators.py --timeout 60 --delay-min 1.0 --delay-max 3.0

# Test with limited number of tickers
python run_technical_indicators.py --limit 10

# Run with visible browser (for debugging)
python run_technical_indicators.py --no-headless

# Custom input/output files
python run_technical_indicators.py --url-file custom_URLs.xlsx --output-file output.xlsx
```

#### Command Line Options

- `--url-file`: Excel file with Ticker and URL columns (default: URL.xlsx)
- `--output-file`: Excel file to update with indicators (default: tickers.xlsx)
- `--headless`: Run browser in headless mode (default: True)
- `--no-headless`: Run browser with visible interface
- `--timeout`: Page load timeout in seconds (default: 30)
- `--delay-min`: Minimum delay between requests (default: 0.5s)
- `--delay-max`: Maximum delay between requests (default: 2.0s)
- `--limit`: Limit number of tickers to process (for testing)

### Web API Usage

The module is integrated into the web server and can be accessed via HTTP:

```bash
# Extract indicators for all tickers
curl "http://localhost:5000/extract-technical-indicators"

# Extract with custom parameters
curl "http://localhost:5000/extract-technical-indicators?limit=10&timeout=60&headless=true"
```

#### API Parameters

- `limit`: Number of tickers to process (integer)
- `timeout`: Page load timeout in seconds (max 60)
- `headless`: Run in headless mode (true/false, default: true)

### Python API Usage

```python
from technical_indicators_extractor import TechnicalIndicatorsExtractor

# Initialize extractor
extractor = TechnicalIndicatorsExtractor(
    headless=True,
    timeout=30,
    delay_min=0.5,
    delay_max=2.0
)

# Extract indicators for a single ticker
result = extractor.extract_indicators_for_ticker(
    ticker="AAPL",
    url="https://www.investing.com/equities/apple-computer-inc-technical"
)

# Process entire URL file
success = extractor.process_tickers_file("URL.xlsx", "tickers.xlsx")

# Clean up resources
extractor.cleanup()
```

## File Structure

### Input File (URL.xlsx)

The URL file must contain the following columns:

| Column | Description | Required |
|--------|-------------|----------|
| Ticker | Stock ticker symbol | Yes |
| URL | Full URL to technical analysis page | Yes |
| Company Name | Company name (optional) | No |

### Output File (tickers.xlsx)

The output file will be updated with the following columns:

#### Core Columns
- `Ticker`: Stock ticker symbol
- `source_url`: URL used for extraction
- `indicator_last_checked`: Timestamp of extraction
- `data_quality`: Quality level (good/partial/mock/fallback)
- `notes`: Additional notes about extraction

#### Technical Indicators Columns
- `Woodies_Pivot`, `Woodies_S1`, `Woodies_S2`, `Woodies_R1`, `Woodies_R2`
- `EMA20`, `SMA50`
- `RSI_14`, `ADX_14`, `ATR_14`  
- `MACD_value`, `MACD_signal`, `MACD_histogram`
- `Bollinger_upper`, `Bollinger_middle`, `Bollinger_lower`
- `Volume_daily`

## Technical Implementation

### Web Scraping Strategy

1. **Multiple User Agents**: Rotates user agents to avoid detection
2. **Rate Limiting**: Configurable delays between requests
3. **Caching**: Pages are cached during a single run
4. **Timeout Handling**: Configurable timeouts for reliability
5. **Retry Logic**: Fallback from requests to Selenium

### Pattern Matching

The module uses regex patterns to extract indicators from page text:

```python
# Example patterns for RSI
rsi_patterns = [
    r'RSI\s*\(14\)[:\s]*([0-9]{1,3}\.?[0-9]*)',
    r'RSI[:\s]*([0-9]{1,3}\.?[0-9]*)',
    r'Relative\s+Strength\s+Index[:\s]*([0-9]{1,3}\.?[0-9]*)'
]
```

### Error Handling

- **Network Errors**: Gracefully handled with mock data fallback
- **Parsing Errors**: Individual indicator failures don't stop processing
- **Browser Errors**: Selenium failures fall back to requests
- **File Errors**: Automatic backup creation before modifications

## Configuration

### Environment Variables

The module respects the following environment variables:

- `TICKERS_FILE`: Default output file (default: "tickers.xlsx")

### Logging

The module uses the centralized logging system:

```python
from logging_config import get_logger
logger = get_logger('stocks_app.technical_indicators')
```

Log levels:
- **INFO**: Progress updates, successful extractions
- **WARNING**: Network failures, fallback usage
- **ERROR**: Critical failures
- **DEBUG**: Detailed extraction information

## Backup and Safety

### Automatic Backups

The module automatically creates backups before modifying files:

```
tickers_backup_YYYYMMDD_HHMMSS.xlsx
```

### Idempotent Operations

Running the extraction multiple times produces consistent results. The module:

- Merges new data with existing data
- Updates existing ticker rows
- Preserves unrelated columns
- Maintains data integrity

## Troubleshooting

### Common Issues

1. **Network Access**: If investing.com is blocked, the module uses mock data
2. **Chrome/Selenium**: If Chrome is unavailable, only requests-based extraction is used
3. **Rate Limiting**: Increase delay parameters if getting blocked
4. **Memory Usage**: For large datasets, process in batches using `--limit`

### Debug Mode

Run with visible browser for debugging:

```bash
python run_technical_indicators.py --no-headless --limit 1
```

### Mock Data Testing

When network is unavailable, the module generates consistent mock data based on ticker hash:

```python
# Mock data is deterministic based on ticker
mock_indicators = extractor._generate_mock_indicators("AAPL")
# Same ticker will always generate the same mock values
```

## Integration with Existing System

The technical indicators module integrates seamlessly with the existing stock analysis system:

1. **Web Dashboard**: Accessible via `/extract-technical-indicators` endpoint
2. **Excel Integration**: Updates the same `tickers.xlsx` used by other modules
3. **Logging**: Uses the same logging system as other components
4. **Configuration**: Respects existing environment variables

The extracted indicators can be used alongside:
- AI stock evaluation
- Sentiment analysis  
- Combined analysis results
- Robinhood price data

## Performance Considerations

### Optimization Tips

1. **Batch Processing**: Use `--limit` for testing and gradual processing
2. **Timing**: Run during off-peak hours to avoid rate limiting
3. **Caching**: Multiple runs benefit from page caching
4. **Headless Mode**: Always use headless mode in production
5. **Timeout Tuning**: Balance between reliability and speed

### Expected Performance

- **Requests-only**: ~2-3 seconds per ticker
- **With Selenium fallback**: ~5-10 seconds per ticker  
- **Mock data**: ~0.1 seconds per ticker
- **Memory usage**: ~50-100MB for 200+ tickers

## Future Enhancements

Potential improvements for the module:

1. **Additional Sites**: Support for Yahoo Finance, TradingView, etc.
2. **More Indicators**: Fibonacci levels, Stochastic, Williams %R
3. **Real-time Updates**: WebSocket connections for live data
4. **Machine Learning**: Pattern recognition for indicator extraction
5. **Database Storage**: PostgreSQL/MySQL backend option
6. **API Rate Limits**: Smarter rate limiting based on site response
7. **Proxy Support**: Rotating proxies for large-scale extraction