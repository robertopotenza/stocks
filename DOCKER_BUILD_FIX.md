# Docker Build Fix: Read-only File System Error

## Problem Statement
Docker build was failing with the following error:
```
RUN echo "nameserver 8.8.8.8" >> /etc/resolv.conf && \
    echo "nameserver 1.1.1.1" >> /etc/resolv.conf
/bin/sh: 1: cannot create /etc/resolv.conf: Read-only file system
```

## Root Cause
Modern Docker containers treat `/etc/resolv.conf` and `/etc/hosts` as read-only file systems managed by the Docker runtime. These files cannot be modified during the build process.

## Solution
Moved DNS and hosts configuration from **build-time** to **runtime** configuration:

### Before (❌ Build-time - FAILED):
```dockerfile
# This fails in modern Docker
RUN echo "nameserver 8.8.8.8" >> /etc/resolv.conf && \
    echo "nameserver 1.1.1.1" >> /etc/resolv.conf
RUN echo "5.254.205.57 www.investing.com investing.com" >> /etc/hosts
```

### After (✅ Runtime - WORKS):
```yaml
# docker-compose.yml
services:
  stocks-app:
    build: .
    dns:
      - 8.8.8.8
      - 1.1.1.1
    extra_hosts:
      - "www.investing.com:5.254.205.57"
      - "investing.com:5.254.205.57"
```

Or with docker run:
```bash
docker run --dns=8.8.8.8 --dns=1.1.1.1 \
           --add-host="www.investing.com:5.254.205.57" \
           your-image
```

## Files Modified
1. **Dockerfile** - Removed problematic resolv.conf/hosts modifications
2. **Dockerfile.fixed** - Removed problematic resolv.conf/hosts modifications  
3. **PRODUCTION_DEPLOYMENT.md** - Updated documentation to show runtime configuration
4. **fix_network_config.py** - Updated to recommend runtime configuration approach

## Verification
- ✅ `docker build -f Dockerfile.fixed` now succeeds
- ✅ `docker compose build` now succeeds  
- ✅ Runtime DNS configuration works correctly
- ✅ No more "Read-only file system" errors

## Best Practices
- Always use Docker runtime flags (--dns, --add-host) for network configuration
- Never attempt to modify /etc/resolv.conf or /etc/hosts in Dockerfiles
- Use docker-compose.yml `dns:` and `extra_hosts:` sections for declarative configuration
- Environment variables can still be set in Dockerfile for application configuration