# Docker Build Troubleshooting Guide

## ✅ Issue Resolved: Read-only File System Error

### Problem That Was Fixed
Previously, the Docker build was failing with:
```
Dockerfile:78 --------------------
77 | # Add public DNS servers to resolv.conf  
78 | >>> RUN echo "nameserver 8.8.8.8" >> /etc/resolv.conf && \
79 | >>> echo "nameserver 1.1.1.1" >> /etc/resolv.conf
80 | --------------------
ERROR: /bin/sh: 1: cannot create /etc/resolv.conf: Read-only file system
```

### Root Cause
Modern Docker containers treat `/etc/resolv.conf` and `/etc/hosts` as read-only file systems managed by the Docker runtime. These files cannot be modified during the build process.

### ✅ Current Status: FIXED
- ✅ Problematic DNS commands have been removed from all Dockerfiles
- ✅ Runtime DNS configuration is properly set up in `docker-compose.yml`
- ✅ Clear documentation added to prevent future issues
- ✅ Both `Dockerfile` and `Dockerfile.fixed` are clean and working

## How to Use Docker Correctly

### ✅ Recommended: Use Docker Compose
```bash
docker-compose up -d
```

This automatically uses:
- `Dockerfile.fixed` (cleaner, no Chrome dependencies)
- Proper DNS configuration (`dns: [8.8.8.8, 1.1.1.1]`)
- Host entries (`extra_hosts` for investing.com)

### ✅ Alternative: Manual Docker Commands
```bash
# Build
docker build -f Dockerfile.fixed -t stocks-extractor .

# Run with proper network configuration
docker run --dns=8.8.8.8 --dns=1.1.1.1 \
           --add-host="www.investing.com:5.254.205.57" \
           --add-host="investing.com:5.254.205.57" \
           stocks-extractor
```

## ❌ What NOT to Do

### Never Try to Modify System Files in Dockerfile
```dockerfile
# ❌ WRONG - This will fail in modern Docker
RUN echo "nameserver 8.8.8.8" >> /etc/resolv.conf
RUN echo "1.2.3.4 example.com" >> /etc/hosts
```

### ✅ Correct Approach - Runtime Configuration
```yaml
# docker-compose.yml
services:
  app:
    build: .
    dns:
      - 8.8.8.8
      - 1.1.1.1
    extra_hosts:
      - "example.com:1.2.3.4"
```

## Verification Commands

### Check for Problematic Commands
```bash
# This should return no results
grep -r "echo.*resolv.conf\|echo.*nameserver.*>>" Dockerfile*
```

### Test Docker Build
```bash
# Should succeed without errors
docker build -f Dockerfile.fixed -t test-build .
```

### Validate Docker Compose
```bash
# Should show valid configuration
docker compose config
```

## Best Practices

1. **Always use runtime configuration** for DNS and hosts
2. **Never modify system files** in Dockerfile build process
3. **Use `Dockerfile.fixed`** for simpler deployments without Chrome
4. **Use `docker-compose.yml`** for complete configuration
5. **Set environment variables** for application configuration, not system configuration

## Files Involved in the Fix

- ✅ `Dockerfile` - Updated with clear warnings about DNS configuration
- ✅ `Dockerfile.fixed` - Clean version without Chrome, proper DNS guidance
- ✅ `docker-compose.yml` - Proper runtime DNS and hosts configuration
- ✅ `README.md` - Added Docker deployment section
- ✅ `DOCKER_BUILD_FIX.md` - Original fix documentation
- ✅ `DOCKER_BUILD_TROUBLESHOOTING.md` - This comprehensive guide

The issue has been completely resolved and documented to prevent future occurrences.