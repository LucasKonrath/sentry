FROM python:3.11-slim

LABEL maintainer="PR Coverage Analyzer Team"
LABEL description="Automated PR coverage analysis and test generation"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY docs/ ./docs/

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash analyzer && \
    chown -R analyzer:analyzer /app

# Switch to non-root user
USER analyzer

# Create directories for logs and results
RUN mkdir -p /app/logs /app/results

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

# Environment variables with defaults
ENV FLASK_APP=src.webhook_server
ENV FLASK_ENV=production
ENV PORT=5000
ENV LOG_LEVEL=INFO

# Run the webhook server by default
CMD ["python", "-m", "src.webhook_server"]
