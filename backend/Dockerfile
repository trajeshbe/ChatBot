FROM python:3.11-slim

WORKDIR /app

# Install base system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Upgrade pip first to avoid warnings
RUN pip install --upgrade pip

COPY requirements.txt .
# Install dependencies (pip 24+ handles hashes automatically)
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# STEP 7: Install Playwright System Dependencies (Debian Trixie Compatible)
# ============================================================================
# Manual installation required because playwright install --with-deps
# fails on Debian Trixie due to obsolete font package names
# Compatible with: playwright==1.41.0, python:3.11-slim
# ============================================================================

RUN apt-get update && apt-get install -y \
    # Core Chromium browser dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    # Critical missing dependencies (from your error)
    libpango-1.0-0 \
    libcairo2 \
    libcairo-gobject2 \
    # X11 and rendering libraries
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcursor1 \
    libxext6 \
    libxi6 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    # GTK and GLib dependencies
    libglib2.0-0 \
    libdbus-1-3 \
    libdbus-glib-1-2 \
    # Font rendering (Debian Trixie equivalents)
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-unifont \
    fontconfig \
    # Additional utilities
    xvfb \
    # Clean up to reduce image size
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# STEP 8: Install Chromium Browser Binary
# ============================================================================
# Install only the browser (no --with-deps flag since we installed deps manually)
# This downloads ~120MB of Chromium browser binaries
# Compatible with: playwright==1.41.0
# ============================================================================

RUN playwright install chromium

# ============================================================================
# STEP 9: Verify Playwright Installation
# ============================================================================
# Optional: Add a verification step to ensure Playwright works
# ============================================================================

RUN python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print(f'Playwright version: {p.chromium.version}'); print('Chromium executable found: OK'); p.stop()"

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
