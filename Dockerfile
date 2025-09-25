# Multi-stage build for optimized stocks extractor with chromium
# Stage 1: Build environment
FROM public.ecr.aws/docker/library/python:3.12-slim AS builder

WORKDIR /app

# Streamlined dependency installation in single layer with effective cleanup
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    gcc \
    ca-certificates \
    dnsutils \
    iputils-ping \
    curl \
    wget \
    unzip \
    # Use chromium instead of full Chrome for smaller size
    chromium \
    chromium-driver \
    # Essential chromium dependencies only
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    # Clean up apt caches in same layer to reduce size
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* /var/log/* /tmp/* /var/tmp/* \
    && apt-get autoremove -y --purge \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Stage 2: Minimal runtime environment
FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app

# Install only runtime dependencies with maximum cleanup
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    dnsutils \
    iputils-ping \
    curl \
    # Chromium runtime essentials
    chromium \
    chromium-driver \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    # Aggressive cleanup in same layer for smaller image
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* /var/log/* /tmp/* /var/tmp/* \
    && apt-get autoremove -y --purge \
    && apt-get clean \
    # Remove unnecessary files to reduce size
    && rm -rf /usr/share/doc/* /usr/share/man/* \
    && find /usr -name "*.pyc" -delete

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Network configuration fixes
# IMPORTANT: DNS and hosts configuration should be done at runtime
# using docker-compose dns settings or --dns and --add-host flags
# DO NOT modify /etc/resolv.conf or /etc/hosts in Docker build - they are read-only

# Create non-root user for security in single layer
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

# Download NLTK data including VADER lexicon for sentiment analysis as the app user
RUN python -c "import nltk; nltk.download('vader_lexicon', quiet=True)"

# Set environment variables for network configuration and chromium
ENV DNS_SERVER=8.8.8.8 \
    LOG_LEVEL=INFO \
    CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main.py"]