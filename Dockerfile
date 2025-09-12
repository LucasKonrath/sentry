FROM ubuntu:22.04

LABEL maintainer="PR Coverage Analyzer Team"
LABEL description="Multi-language automated PR coverage analysis and test generation"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.11
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    rm -rf /var/lib/apt/lists/*

# Install Java 17 (LTS)
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk maven && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js 18 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest

# Install .NET 8 SDK
RUN wget https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y dotnet-sdk-8.0 && \
    rm packages-microsoft-prod.deb && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV DOTNET_ROOT=/usr/share/dotnet
ENV PATH=$PATH:$JAVA_HOME/bin:$DOTNET_ROOT

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY docs/ ./docs/
COPY examples/ ./examples/
COPY build.sh .
COPY *.md ./

# Make build script executable
RUN chmod +x build.sh

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash analyzer && \
    chown -R analyzer:analyzer /app

# Create workspace directory for analyzed projects
RUN mkdir -p /workspace && \
    chown -R analyzer:analyzer /workspace

# Switch to non-root user
USER analyzer

# Set default environment variables for multi-language support
ENV PYTHONPATH=/app/src
ENV GITHUB_TOKEN=""
ENV OPENAI_API_KEY=""
ENV COVERAGE_THRESHOLD=80

# Create directories for logs and results  
RUN mkdir -p /app/logs /app/results

# Create workspace volume for analyzed projects
VOLUME ["/workspace"]
WORKDIR /workspace

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Expose port for webhook server
EXPOSE 5000

# Environment variables with defaults for webhook server
ENV FLASK_APP=src.webhook_server
ENV FLASK_ENV=production  
ENV PORT=5000
ENV LOG_LEVEL=INFO

# Default command - can be overridden for different use cases
# For webhook server: docker run <image>
# For CLI analysis: docker run <image> /app/build.sh --repo-url <url> --pr-number <num>
CMD ["python", "-m", "src.webhook_server"]
