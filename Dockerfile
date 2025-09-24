# Use Python 3.12 slim image for smaller footprint
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Chrome and ChromeDriver
RUN apt-get update && apt-get install -y \
    gcc \
    ca-certificates \
    dnsutils \
    iputils-ping \
    curl \
    wget \
    gnupg \
    unzip \
    # Chrome dependencies
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libxss1 \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f3 | cut -d '.' -f1) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}") \
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# Upgrade pip and setup certificates
RUN pip install --upgrade pip

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies with trusted hosts for SSL issues
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Download NLTK data including VADER lexicon for sentiment analysis
RUN python -c "import nltk; nltk.download('vader_lexicon', quiet=True)"

# Copy application code
COPY . .

# Network configuration fixes
# Add public DNS servers to resolv.conf
RUN echo "nameserver 8.8.8.8" >> /etc/resolv.conf && \
    echo "nameserver 1.1.1.1" >> /etc/resolv.conf

# Add investing.com to hosts file for reliability  

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Change ownership of the app directory to the app user
RUN chown -R app:app /app

USER app

# Set environment variables for network configuration
ENV DNS_SERVER=8.8.8.8
ENV LOG_LEVEL=INFO

# Run the application
CMD ["python", "main.py"]