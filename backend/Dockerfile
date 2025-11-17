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
# STEP 7 & 8: Install Playwright with Complete Dependencies
# ============================================================================
# Use playwright install-deps for system dependencies, then install browser
# This is the recommended approach from Playwright documentation
# Compatible with: playwright==1.41.0, python:3.11-slim
# ============================================================================

# First, install Chromium browser binary
RUN playwright install chromium

# Then, install all required system dependencies using the official method
# This ensures compatibility and installs all needed libraries
RUN playwright install-deps chromium

# ============================================================================
# STEP 9: Verify Playwright Installation
# ============================================================================
# Test that Playwright can be imported and browser is accessible
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
