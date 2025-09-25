# Improved Technical Indicators Extractor Guide

This guide explains the enhanced features of the Technical Indicators Extractor that address HTTP 403 (Forbidden) errors and improve reliability.

## Key Improvements

### 1. Enhanced Request Resilience 

**Header Profile Rotation**
- 6 different browser profiles (Chrome, Firefox, Safari)
- Realistic headers including Referer, Sec-Fetch-* headers
- Automatic rotation to avoid detection

**Retry Strategy with Exponential Backoff**
- 3 automatic retries for failed requests
- Exponential backoff for rate limiting (429) errors
- Intelligent retry logic for different error types

**Proxy Support**
- Automatic detection of `HTTP_PROXY` and `HTTPS_PROXY` environment variables
- Session-based connection pooling
- Corporate firewall compatibility

### 2. Selenium Fallback

**Container-Ready Selenium**
- Enhanced Dockerfile with Chrome/ChromeDriver installation
- Headless Chrome with anti-detection measures
- Undetected-chromedriver support for reduced blocking

**Smart Fallback Logic**
- Automatic fallback to Selenium on 403 errors
- Configurable Selenium enable/disable
- Optimized Chrome options for containers

### 3. Better Error Handling

**Clear Error Classification**
- 403 errors clearly marked as "BLOCKED" not DNS failures
- Specific handling for rate limiting (429)
- Enhanced DNS resolution error reporting

**Comprehensive Logging**
- Detailed request/response information
- User-Agent tracking for debugging
- Network configuration diagnostics

## Usage Examples

### Basic Usage (Requests Only)
```python
from technical_indicators_extractor import TechnicalIndicatorsExtractor

# Disable Selenium for pure HTTP requests
extractor = TechnicalIndicatorsExtractor(enable_selenium=False)
data = extractor.extract_indicators_for_ticker("AAPL")
```

### With Selenium Fallback
```python
# Enable Selenium fallback for blocked requests
extractor = TechnicalIndicatorsExtractor(
    enable_selenium=True,
    headless=True,
    timeout=30
)
data = extractor.extract_indicators_for_ticker("AAPL")
```

### With Proxy Configuration
```bash
# Set proxy environment variables
export HTTPS_PROXY=http://proxy.company.com:8080
export HTTP_PROXY=http://proxy.company.com:8080

# Run extractor - proxy will be automatically detected
python technical_indicators_extractor.py --ticker AAPL
```

### Custom Configuration
```python
extractor = TechnicalIndicatorsExtractor(
    headless=True,           # Run browser in headless mode
    timeout=45,              # Request timeout in seconds
    delay_min=1.0,           # Minimum delay between requests
    delay_max=3.0,           # Maximum delay between requests
    enable_selenium=True     # Enable Selenium fallback
)
```

## Container Deployment

The enhanced Dockerfile includes:
- Google Chrome stable
- ChromeDriver (auto-matched version)
- Network diagnostic tools
- DNS configuration fixes

### Building the Container
```bash
docker build -t stocks-extractor .
```

### Running with Proxy
```bash
docker run -e HTTPS_PROXY=http://proxy:8080 stocks-extractor
```

### Running with Custom DNS
```bash
docker run -e DNS_SERVER=8.8.8.8 stocks-extractor
```

## Troubleshooting

### 403 Forbidden Errors
1. **Check logs** for "BLOCKED" messages - this indicates bot detection
2. **Enable Selenium fallback** with `enable_selenium=True`
3. **Configure proxy** if behind corporate firewall
4. **Increase delays** between requests to avoid rate limiting

### DNS Resolution Issues
1. **Set DNS servers**: `export DNS_SERVER=8.8.8.8`
2. **Add to hosts file**: `echo "5.254.205.57 www.investing.com" >> /etc/hosts`
3. **Check network connectivity** with `ping google.com`

### Selenium Issues in Container
1. **Verify Chrome installation**: `google-chrome --version`
2. **Check ChromeDriver**: `chromedriver --version`
3. **Run with --no-sandbox**: Automatically configured in container
4. **Enable verbose logging**: `export LOG_LEVEL=DEBUG`

#### Container-Specific Timeout Issues
The enhanced Selenium implementation includes specific fixes for container environments:

**Progressive Timeout Strategy:**
- Login attempts use increasing timeouts: 15s → 30s → 45s
- Page load timeout minimum of 60 seconds for containers
- Implicit wait increased to 15 seconds for slower containers

**Enhanced Chrome Options:**
- Memory management: `--memory-pressure-off`, `--max_old_space_size=4096`
- Single-process mode for better resource management
- Additional stability flags for ephemeral containers

**Driver Health Monitoring:**
- Automatic health checks before operations
- Chrome process crash detection and recovery
- Version compatibility validation

**Recovery Mechanisms:**
- Automatic driver recreation after crashes
- Multiple retry attempts with smart recovery
- Enhanced cleanup with forced process termination

## Configuration Options

### Environment Variables
- `HTTP_PROXY` / `HTTPS_PROXY`: Proxy server configuration
- `DNS_SERVER`: Custom DNS server (default: 8.8.8.8)
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `investing_login` / `investing_password`: Investing.com credentials (optional)

### Extractor Parameters
- `headless`: Run browser in headless mode (default: True)
- `timeout`: Request/page load timeout in seconds (default: 30, min 60 for Selenium)
- `delay_min/delay_max`: Random delay range between requests (default: 0.5-2.0s)
- `enable_selenium`: Enable Selenium fallback (default: True)

## Monitoring and Debugging

### Key Log Messages
- `📡 Attempting to fetch` - Starting HTTP request
- `🚫 Access BLOCKED (403)` - Bot detection/rate limiting
- `🤖 Attempting to fetch` - Selenium fallback activated
- `✅ Successfully fetched` - Request completed successfully
- `🔐 Attempting to log into Investing.com` - Login attempt started
- `⏱️ Investing.com login timeout` - Login timeout (expected in containers)
- `🔄 Attempting to recover Selenium driver` - Driver recovery in progress

### Container Performance Indicators
- **Chrome version compatibility**: Logged at startup for debugging
- **Driver health checks**: Automatic validation before operations
- **Progressive timeouts**: Multiple attempts with increasing timeouts
- **Recovery success rate**: Monitor driver recreation success

### Performance Metrics
- Header rotation: 6 unique profiles available
- Retry attempts: Up to 3 per URL
- Cache hit rate: Monitored via cache size
- Fallback usage: Selenium activation frequency
- **Container stability**: Enhanced timeout handling for ephemeral environments

## Best Practices

1. **Start with requests-only** mode for testing
2. **Enable Selenium fallback** for production reliability
3. **Configure appropriate delays** based on target site behavior
4. **Monitor logs** for blocking patterns
5. **Use proxy** in corporate environments
6. **Test container deployment** before production use

### Container Deployment Best Practices
7. **Use minimum 2GB RAM** for Chrome processes in containers
8. **Allow sufficient timeout values** (minimum 60 seconds for page loads)
9. **Monitor Chrome process health** via health check endpoints
10. **Enable progressive timeout strategy** for unreliable networks
11. **Configure proper cleanup** to prevent resource leaks
12. **Use health checks** to restart containers with crashed drivers

## Testing

Run the test suite to validate improvements:
```bash
python test_improvements.py        # Test individual features
python test_complete_extractor.py  # Test complete functionality
python debug_extractor.py --limit 1 --no-headless  # Test Selenium with visible browser
```

### Container-Specific Testing
```bash
# Test enhanced Selenium timeout handling
python -c "
from technical_indicators_extractor import TechnicalIndicatorsExtractor
extractor = TechnicalIndicatorsExtractor(headless=True, enable_selenium=True)
version_info = extractor._get_chrome_version_info()
print(f'Chrome/Driver versions: {version_info}')
extractor.cleanup()
"
```

Expected results:
- Header rotation: ✅ Working
- Proxy support: ✅ Working  
- Requests resilience: ✅ Working
- Error handling: ✅ Working
- Cache functionality: ✅ Working
- **Container timeout handling**: ✅ Enhanced
- **Driver recovery**: ✅ Automatic
- **Chrome health monitoring**: ✅ Active