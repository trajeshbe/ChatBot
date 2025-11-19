# Playwright Official Docker Image
# Base: Microsoft's official Playwright image with Python and Chromium pre-installed
# Using Jammy (Ubuntu 22.04) which is officially supported and has no t64 transition issues
# This solves the library compatibility problems we had with Ubuntu 24.04

FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

WORKDIR /app

# Install PostgreSQL client libraries (required for psycopg2)
# Note: Playwright image is based on Ubuntu, so we can use apt-get
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Copy and install Python dependencies
COPY requirements.txt .

# Install Python packages (including playwright==1.48.0)
RUN pip install --no-cache-dir -r requirements.txt

# NOTE: Playwright browsers are already installed in the base image at /ms-playwright/
# The base image mcr.microsoft.com/playwright/python:v1.48.0-jammy includes:
# - chromium-1140 (compatible with Ubuntu 22.04/Jammy)
# - firefox-1465
# - webkit-2083
# We use PLAYWRIGHT_BROWSERS_PATH=/ms-playwright env var to point to these browsers
# DO NOT run 'playwright install' as it may download incompatible versions

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /tmp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
