#!/bin/bash
# Network configuration for technical indicators extractor

# Set DNS server
export DNS_SERVER=8.8.8.8

# Configure proxy if needed (uncomment and modify as needed)
# export HTTP_PROXY=http://proxy.company.com:8080
# export HTTPS_PROXY=http://proxy.company.com:8080
# export NO_PROXY=localhost,127.0.0.1,github.com

# Disable SSL verification if needed (not recommended for production)
# export PYTHONHTTPSVERIFY=0

# Set debug logging
export LOG_LEVEL=DEBUG

echo "✅ Network environment configured"
echo "   DNS Server: $DNS_SERVER"
echo "   HTTP Proxy: ${HTTP_PROXY:-<not set>}"
echo "   HTTPS Proxy: ${HTTPS_PROXY:-<not set>}"
