# Use Python 3.12 slim image for smaller footprint
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for pandas/numpy if needed
RUN apt-get update && apt-get install -y \
    gcc \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setup certificates
RUN pip install --upgrade pip

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies with trusted hosts for SSL issues
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app
USER app

# Run the application
CMD ["python", "main.py"]