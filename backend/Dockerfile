# Ubuntu-based Dockerfile for better Playwright compatibility
# Base: Ubuntu 24.04 LTS with Python 3.12 (default)
FROM ubuntu:24.04

WORKDIR /app

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.12 (default) and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    gcc \
    g++ \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3 as default python command
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Upgrade pip
RUN python -m pip install --upgrade pip

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Install Playwright with Complete Dependencies (Ubuntu Native)
# ============================================================================
# Ubuntu 24.04 LTS has full support for Playwright's dependency installer
# This will install all required system libraries natively
# ============================================================================

# Install Chromium browser with all system dependencies
RUN playwright install --with-deps chromium

# ============================================================================
# Verify Playwright Installation
# ============================================================================

RUN python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright imported successfully')" && \
    playwright --version && \
    echo "✅ Playwright installation verified"

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
