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

# Install Playwright browsers AND system dependencies
# This automatically installs all required system libraries
RUN playwright install --with-deps chromium

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
