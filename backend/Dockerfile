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
    # Playwright system dependencies (Ubuntu 24.04 compatible)
    libnss3 \
    libnspr4 \
    libatk1.0-0t64 \
    libatk-bridge2.0-0t64 \
    libcups2t64 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2t64 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0t64 \
    libxshmfence1 \
    fonts-liberation \
    fonts-noto-color-emoji \
    libglib2.0-0t64 \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3 as default python command
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Create and activate virtual environment (required for Ubuntu 24.04 PEP 668)
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip in virtual environment
RUN pip install --upgrade pip

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Install Playwright Browser (Ubuntu 24.04)
# ============================================================================
# System dependencies installed manually above due to Ubuntu 24.04 package renames
# (libasound2 -> libasound2t64, etc.)
# ============================================================================

# Install Chromium browser only (dependencies already installed)
RUN playwright install chromium

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
