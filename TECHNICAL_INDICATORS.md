# Technical Indicators Extraction Module - Twelve Data API Edition

This module provides comprehensive technical indicators extraction using the reliable Twelve Data API. It extracts key technical analysis indicators and updates the Excel files with the results.

## Features

### Extracted Indicators

The module extracts the following technical indicators using the Twelve Data API:

#### Woodie's Pivot Points
- **Pivot**: Main pivot point level (calculated from historical data)
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

The module implements a reliable API-based approach with fallback strategies:

1. **Primary Method**: Twelve Data API (fast and reliable)
2. **Fallback Method**: Mock data (for testing when API is unavailable)

#### Data Quality Levels
- **excellent**: 10+ indicators successfully extracted from API
- **good**: 5-9 indicators successfully extracted from API
- **partial**: 1-4 indicators successfully extracted from API
- **mock**: Mock data used (no API key or API unavailable)
- **api**: Standard API response with good data quality

## Setup

### API Key Configuration

Get your free API key from [Twelve Data](https://twelvedata.com/):

1. Sign up for a free account
2. Generate your API key
3. Set the environment variable:

```bash
export TWELVEDATA_API_KEY=your_api_key_here
```

Or set it in Railway/deployment platform:
- Variable name: `TWELVEDATA_API_KEY` 
- Variable value: `your_api_key_here`

### Rate Limits

The free tier includes:
- 800 API calls per day
- 8 API calls per minute
- Access to all technical indicators

The module automatically implements rate limiting with configurable delays between requests.

## Usage

### Command Line Interface

```bash
# Basic usage with defaults
python technical_indicators_extractor.py

# Run with custom parameters
python technical_indicators_extractor.py --delay-min 1.0 --delay-max 3.0

# Test with limited number of tickers
python technical_indicators_extractor.py --limit 10

# Custom input/output files
python technical_indicators_extractor.py --url-file custom_URLs.xlsx --output-file output.xlsx

# Specify API key directly
python technical_indicators_extractor.py --api-key your_api_key_here
```

#### Command Line Options

- `--url-file`: Excel file with Ticker column (default: URL.xlsx)
- `--output-file`: Excel file to update with indicators (default: tickers.xlsx)
- `--api-key`: Twelve Data API key (or set TWELVEDATA_API_KEY env var)
- `--delay-min`: Minimum delay between requests (default: 1.0s)
- `--delay-max`: Maximum delay between requests (default: 2.0s)
- `--limit`: Limit number of tickers to process (for testing)

### Web API Usage

The module is integrated into the web server and can be accessed via HTTP:

```bash
# Extract indicators for all tickers
curl "http://localhost:5000/extract-technical-indicators"

# Extract with custom parameters
curl "http://localhost:5000/extract-technical-indicators?limit=10&api_key=your_key"
```

#### API Parameters

- `limit`: Number of tickers to process (integer)
- `api_key`: Twelve Data API key (optional if set via environment)

### Python API Usage

```python
from technical_indicators_extractor import TechnicalIndicatorsExtractor

# Initialize extractor
extractor = TechnicalIndicatorsExtractor(
    api_key="your_api_key_here",
    delay_min=1.0,
    delay_max=2.0
)

# Extract indicators for a single ticker
result = extractor.extract_indicators_for_ticker("AAPL")

# Process entire file (only needs Ticker column)
success = extractor.process_tickers_file("URL.xlsx", "tickers.xlsx")

# Clean up resources (minimal cleanup needed)
extractor.cleanup()
```

## File Structure

### Input File (URL.xlsx)

The URL file now only requires the Ticker column:

| Column | Description | Required |
|--------|-------------|----------|
| Ticker | Stock ticker symbol | Yes |
| URL | No longer used (kept for compatibility) | No |
| Company Name | Company name (optional) | No |

### Output File (tickers.xlsx)

The output file will be updated with the following columns:

#### Core Columns
- `Ticker`: Stock ticker symbol
- `source_url`: API source identifier
- `indicator_last_checked`: Timestamp of extraction
- `data_quality`: Quality level (excellent/good/partial/mock/api)
- `notes`: Additional notes about extraction

#### Technical Indicators Columns
- `Woodies_Pivot`, `Woodies_S1`, `Woodies_S2`, `Woodies_R1`, `Woodies_R2`
- `EMA20`, `SMA50`
- `RSI_14`, `ADX_14`, `ATR_14`  
- `MACD_value`, `MACD_signal`, `MACD_histogram`
- `Bollinger_upper`, `Bollinger_middle`, `Bollinger_lower`
- `Volume_daily`

## Technical Implementation

### API Integration Strategy

1. **Rate Limiting**: Configurable delays between requests (1-2 seconds default)
2. **Error Handling**: Graceful fallback to mock data when API is unavailable
3. **Data Validation**: Robust parsing of API responses with type checking
4. **Caching**: No caching needed - API responses are always fresh

### API Endpoints Used

The module uses the following Twelve Data API endpoints:

```python
# Current price and historical data
GET /time_series?symbol={ticker}&interval=1day&outputsize=10

# Technical indicators
GET /rsi?symbol={ticker}&interval=1day&time_period=14
GET /ema?symbol={ticker}&interval=1day&time_period=20
GET /sma?symbol={ticker}&interval=1day&time_period=50
GET /macd?symbol={ticker}&interval=1day&fast_period=12&slow_period=26&signal_period=9
GET /bbands?symbol={ticker}&interval=1day&time_period=20&sd=2
GET /adx?symbol={ticker}&interval=1day&time_period=14
GET /atr?symbol={ticker}&interval=1day&time_period=14
```

### Error Handling

- **API Errors**: Individual indicator failures don't stop processing
- **Network Errors**: Gracefully handled with mock data fallback
- **Rate Limits**: Automatic delay adjustment and retry logic
- **Invalid Tickers**: Marked as 'N/A' without stopping the process

## Configuration

### Environment Variables

The module respects the following environment variables:

- `TWELVEDATA_API_KEY`: Your Twelve Data API key (required)
- `api_key`: Alternative environment variable name (for Railway)
- `TICKERS_FILE`: Default output file (default: "tickers.xlsx")

### Logging

The module uses the centralized logging system:

```python
from logging_config import get_logger
logger = get_logger('stocks_app.technical_indicators')
```

Log levels:
- **INFO**: Progress updates, successful extractions
- **WARNING**: API failures, fallback usage
- **ERROR**: Critical failures
- **DEBUG**: Detailed API information

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

1. **No API Key**: If no API key is provided, the module uses mock data for testing
2. **Rate Limiting**: Increase delay parameters if hitting rate limits
3. **Invalid Tickers**: Invalid tickers are marked as 'N/A' and logged
4. **Network Issues**: API failures gracefully fall back to mock data

### Debug Mode

Check your API usage and configuration:

```bash
# Test with a single ticker
python technical_indicators_extractor.py --limit 1

# Check API key configuration
echo $TWELVEDATA_API_KEY
```

### Mock Data Testing

When API is unavailable, the module generates consistent mock data based on ticker hash:

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
- Current price data from Twelve Data API

## Performance Considerations

### Optimization Tips

1. **Batch Processing**: Use `--limit` for testing and gradual processing
2. **Rate Limiting**: Respect API limits with appropriate delays
3. **API Efficiency**: Single API call per indicator per ticker
4. **Memory Usage**: Minimal memory footprint compared to web scraping

### Expected Performance

- **API-based**: ~2-3 seconds per ticker (including delays)
- **Mock data**: ~0.1 seconds per ticker
- **Memory usage**: ~10-20MB for 200+ tickers
- **Network usage**: ~1KB per API call

## Migration from Web Scraping

### Key Improvements

1. **Reliability**: No more web scraping failures or browser crashes
2. **Speed**: Faster and more consistent than browser automation
3. **Maintenance**: No browser dependencies or version conflicts
4. **Scalability**: Better rate limiting and error handling
5. **Data Quality**: Consistent, structured data from reliable API

### Backward Compatibility

The module maintains backward compatibility:
- Same command-line interface
- Same file formats
- Same indicator names and structures
- Same logging and error reporting

## API Costs and Limits

### Free Tier Limitations

- 800 API calls per day
- 8 API calls per minute
- All technical indicators included

### Usage Optimization

For a typical portfolio of 50 stocks:
- ~10 API calls per stock (historical data + indicators)
- ~500 total API calls per extraction
- Can run once per day within free limits

### Paid Plans

Twelve Data offers paid plans for higher limits:
- Basic: $10/month (5,000 calls/day)
- Standard: $30/month (20,000 calls/day)
- Professional: $50/month (100,000 calls/day)

## Future Enhancements

Potential improvements for the module:

1. **Additional Indicators**: Fibonacci levels, Stochastic, Williams %R
2. **Multiple Timeframes**: Support for different interval periods
3. **Real-time Updates**: WebSocket connections for live data
4. **Data Caching**: Redis/memory caching for frequently accessed data
5. **Database Storage**: PostgreSQL/MySQL backend option
6. **Alternative APIs**: Support for multiple data providers
7. **Custom Indicators**: User-defined technical analysis formulas