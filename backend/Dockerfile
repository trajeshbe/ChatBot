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

# Install Playwright system dependencies manually (compatible with Debian trixie)
RUN apt-get update && apt-get install -y \
    # Core libraries for Chromium
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    # Fonts
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-unifont \
    # Additional dependencies
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers (without --with-deps since we installed deps manually)
RUN playwright install chromium

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
