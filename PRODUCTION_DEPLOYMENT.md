# Production Deployment Guide for Technical Indicators Extractor

## Problem Statement

The technical indicators extractor is falling back to mock data in production due to network connectivity issues. This guide provides comprehensive solutions to diagnose and fix the problem.

## Root Cause Analysis

**Primary Issue**: DNS Resolution Failure
- The production container cannot resolve `www.investing.com` 
- Error: `Failed to resolve 'www.investing.com' ([Errno -5] No address associated with hostname)`
- This triggers the fallback mechanism to use mock data instead of real market data

**Contributing Factors**:
1. Missing or misconfigured DNS servers in container environment
2. Network policy restrictions blocking external DNS queries
3. Firewall rules preventing access to investing.com
4. Missing proxy configuration in corporate environments

## Quick Diagnosis

### Health Check
Run the health check to quickly identify issues:
```bash
python health_check.py
```

### Full Diagnosis
For comprehensive analysis, run:
```bash
python production_debug.py --full-test
```

## Production Fixes

### Option 1: Docker Container Fixes (Recommended)

#### A. Use the Fixed Dockerfile
Replace your current Dockerfile with `Dockerfile.fixed`:
```bash
docker build -f Dockerfile.fixed -t stocks-extractor .
```

#### B. Use Docker Compose with Network Configuration
```bash
# Deploy with network fixes
docker-compose up -d

# Or run debug container
docker-compose --profile debug up stocks-debug
```

### Option 2: Manual Container Configuration

#### Add DNS Servers (Runtime Configuration)
```bash
# Use Docker runtime DNS configuration instead of modifying /etc/resolv.conf
# /etc/resolv.conf is read-only in modern Docker containers

# Method 1: Docker run with DNS flags
docker run --dns=8.8.8.8 --dns=1.1.1.1 stocks-extractor

# Method 2: Docker-compose (preferred - already configured in docker-compose.yml)
# dns:
#   - 8.8.8.8 
#   - 1.1.1.1
```

#### Add Hosts File Entry (Runtime Configuration)
```bash
# Use Docker runtime hosts configuration instead of modifying /etc/hosts
# /etc/hosts is read-only in modern Docker containers

# Method 1: Docker run with add-host flags
docker run --add-host="www.investing.com:5.254.205.57" --add-host="investing.com:5.254.205.57" stocks-extractor

# Method 2: Docker-compose (preferred - already configured in docker-compose.yml)  
# extra_hosts:
#   - "www.investing.com:5.254.205.57"
#   - "investing.com:5.254.205.57"
```

#### Set Environment Variables
```bash
export DNS_SERVER=8.8.8.8
export LOG_LEVEL=DEBUG
```

### Option 3: Proxy Configuration (Corporate Networks)

If behind a corporate firewall:
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1,github.com
```

## Container Orchestration Examples

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stocks-extractor
spec:
  template:
    spec:
      dnsPolicy: "None"
      dnsConfig:
        nameservers:
          - 8.8.8.8
          - 1.1.1.1
      containers:
      - name: stocks-extractor
        image: stocks-extractor:latest
        env:
        - name: DNS_SERVER
          value: "8.8.8.8"
        - name: LOG_LEVEL
          value: "DEBUG"
        volumeMounts:
        - name: hosts-config
          mountPath: /etc/hosts.custom
      volumes:
      - name: hosts-config
        configMap:
          name: hosts-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: hosts-config
data:
  hosts: |
    127.0.0.1 localhost
    5.254.205.57 www.investing.com investing.com
```

### Docker Swarm
```yaml
version: '3.8'
services:
  stocks-extractor:
    image: stocks-extractor:latest
    deploy:
      replicas: 1
    dns:
      - 8.8.8.8
      - 1.1.1.1
    environment:
      - DNS_SERVER=8.8.8.8
      - LOG_LEVEL=DEBUG
    extra_hosts:
      - "www.investing.com:5.254.205.57"
      - "investing.com:5.254.205.57"
```

## Alternative Solutions

### Option A: Switch to Yahoo Finance
If investing.com remains inaccessible, consider switching to Yahoo Finance:
```python
# Example URL pattern
yahoo_url = "https://finance.yahoo.com/quote/{ticker}/key-statistics"
```

### Option B: Use API-Based Sources
Consider using structured APIs like Alpha Vantage:
```bash
# Requires API key
export ALPHA_VANTAGE_API_KEY=your_key_here
```

### Option C: Enhanced Mock Data
Improve mock data quality with historical patterns:
```python
# Enable enhanced mock data mode
export USE_ENHANCED_MOCK_DATA=true
```

## Monitoring and Alerting

### Health Check Endpoint
Add to your monitoring system:
```bash
# Returns 0 if healthy, 1 if issues
python health_check.py
```

### Log Monitoring
Monitor these log patterns for production issues:
- `DNS Resolution Failed`
- `Mock data - PRODUCTION ISSUE`
- `data_quality: mock`

### Metrics to Track
- Percentage of tickers using mock data
- DNS resolution success rate
- HTTP request success rate
- Average extraction time per ticker

## Testing the Fix

### 1. Verify DNS Resolution
```bash
python -c "import socket; print(socket.gethostbyname('www.investing.com'))"
```

### 2. Test HTTP Connectivity
```bash
python -c "import requests; print(requests.get('https://www.investing.com', timeout=5).status_code)"
```

### 3. Run Extraction Test
```bash
python debug_extractor.py --limit 1
```

### 4. Check Data Quality
Look for `data_quality: good` instead of `data_quality: mock` in the output.

## Troubleshooting

### Common Issues

1. **Still getting mock data after fixes**
   - Check container restart: `docker-compose restart`
   - Verify environment variables: `env | grep -E '(DNS|PROXY)'`
   - Check hosts file: `cat /etc/hosts | grep investing`

2. **Permission denied errors**
   - Run with appropriate privileges for /etc/hosts modification
   - Use init containers for setup in Kubernetes

3. **Proxy authentication required**
   - Add credentials: `export HTTPS_PROXY=http://user:pass@proxy:port`

4. **SSL certificate errors**
   - Temporarily: `export PYTHONHTTPSVERIFY=0` (not recommended for production)
   - Better: Add corporate CA certificates to container

### Debug Commands
```bash
# Check DNS configuration
cat /etc/resolv.conf

# Check hosts file
cat /etc/hosts

# Test network connectivity
ping -c 3 8.8.8.8

# Test domain resolution
nslookup www.investing.com

# Test HTTP connectivity
curl -I https://www.investing.com
```

## Success Criteria

After implementing fixes, you should see:
- ✅ `data_quality: good` or `data_quality: partial` in extraction results
- ✅ No `Mock data - PRODUCTION ISSUE` warnings in logs
- ✅ DNS resolution working: `python health_check.py` returns exit code 0
- ✅ Real market data being extracted instead of mock values

## Support

If issues persist after trying these fixes:
1. Run `python production_debug.py --full-test` and share the output
2. Check your network security policies
3. Contact your infrastructure team for DNS/proxy configuration
4. Consider alternative data sources as temporary workaround