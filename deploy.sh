#!/bin/bash

# PR Coverage Analyzer Deployment Script
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-development}
PROJECT_DIR=$(dirname "$(readlink -f "$0")")
SCRIPT_DIR="$PROJECT_DIR/scripts"

echo "🚀 Deploying PR Coverage Analyzer - Environment: $ENVIRONMENT"
echo "📂 Project Directory: $PROJECT_DIR"

# Load environment-specific configuration
if [ -f "config/${ENVIRONMENT}.env" ]; then
    echo "📋 Loading configuration from config/${ENVIRONMENT}.env"
    export $(cat "config/${ENVIRONMENT}.env" | grep -v '^#' | xargs)
else
    echo "⚠️  No configuration file found for $ENVIRONMENT"
    echo "📝 Please create config/${ENVIRONMENT}.env or use config/env.example as template"
fi

# Check required environment variables
check_env_var() {
    if [ -z "${!1}" ]; then
        echo "❌ Error: $1 environment variable is required but not set"
        exit 1
    fi
}

echo "🔍 Checking required environment variables..."
check_env_var "GITHUB_TOKEN"
check_env_var "OPENAI_API_KEY"

# Function to deploy with Docker
deploy_docker() {
    echo "🐳 Deploying with Docker..."
    
    # Build the image
    echo "🔨 Building Docker image..."
    docker build -t pr-coverage-analyzer:$ENVIRONMENT .
    
    # Stop existing container if running
    echo "🛑 Stopping existing container..."
    docker stop pr-coverage-analyzer-$ENVIRONMENT || true
    docker rm pr-coverage-analyzer-$ENVIRONMENT || true
    
    # Run the new container
    echo "▶️  Starting new container..."
    docker run -d \
        --name pr-coverage-analyzer-$ENVIRONMENT \
        --restart unless-stopped \
        -p "${PORT:-5000}:5000" \
        --env-file "config/${ENVIRONMENT}.env" \
        -v "$PROJECT_DIR/logs:/app/logs" \
        -v "$PROJECT_DIR/results:/app/results" \
        -v "$PROJECT_DIR/config:/app/config:ro" \
        pr-coverage-analyzer:$ENVIRONMENT
    
    echo "✅ Docker deployment complete!"
}

# Function to deploy with Docker Compose
deploy_compose() {
    echo "🐳 Deploying with Docker Compose..."
    
    # Copy environment file for compose
    cp "config/${ENVIRONMENT}.env" .env
    
    # Deploy with compose
    docker-compose down || true
    docker-compose up --build -d
    
    echo "✅ Docker Compose deployment complete!"
}

# Function to deploy locally
deploy_local() {
    echo "💻 Deploying locally..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "🐍 Creating Python virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install/update dependencies
    echo "📦 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create necessary directories
    mkdir -p logs results
    
    # Start the webhook server
    echo "🚀 Starting webhook server..."
    if [ "$ENVIRONMENT" = "development" ]; then
        export FLASK_ENV=development
        export DEBUG=True
        python -m src.webhook_server
    else
        # Production deployment with gunicorn
        pip install gunicorn
        gunicorn --bind 0.0.0.0:${PORT:-5000} \
                 --workers 4 \
                 --access-logfile logs/access.log \
                 --error-logfile logs/error.log \
                 --daemon \
                 "src.webhook_server:app"
        echo "✅ Production server started with gunicorn"
    fi
}

# Function to deploy to cloud platforms
deploy_cloud() {
    echo "☁️  Deploying to cloud platform..."
    
    case "$CLOUD_PROVIDER" in
        "aws")
            deploy_aws
            ;;
        "gcp")
            deploy_gcp
            ;;
        "azure")
            deploy_azure
            ;;
        "heroku")
            deploy_heroku
            ;;
        *)
            echo "❌ Unsupported cloud provider: $CLOUD_PROVIDER"
            echo "📝 Supported providers: aws, gcp, azure, heroku"
            exit 1
            ;;
    esac
}

# AWS deployment (placeholder)
deploy_aws() {
    echo "🚀 Deploying to AWS..."
    echo "📝 This would deploy using AWS Lambda, ECS, or EC2"
    echo "📚 See docs/aws-deployment.md for detailed instructions"
}

# Main deployment logic
case "$ENVIRONMENT" in
    "development"|"dev")
        deploy_local
        ;;
    "docker")
        deploy_docker
        ;;
    "compose")
        deploy_compose
        ;;
    "production"|"prod")
        if [ -n "$CLOUD_PROVIDER" ]; then
            deploy_cloud
        elif [ -f "docker-compose.yml" ]; then
            deploy_compose
        else
            deploy_local
        fi
        ;;
    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        echo "📝 Supported environments: development, docker, compose, production"
        exit 1
        ;;
esac

# Health check
echo "🏥 Performing health check..."
sleep 5

if curl -f "http://localhost:${PORT:-5000}/health" >/dev/null 2>&1; then
    echo "✅ Health check passed - Service is running!"
    
    # Display useful information
    echo ""
    echo "📊 Deployment Summary:"
    echo "   Environment: $ENVIRONMENT"
    echo "   Port: ${PORT:-5000}"
    echo "   Health URL: http://localhost:${PORT:-5000}/health"
    echo "   Webhook URL: http://localhost:${PORT:-5000}/webhook"
    echo "   Logs: $PROJECT_DIR/logs/"
    
    if [ "$ENVIRONMENT" = "development" ]; then
        echo ""
        echo "🛠️  Development Mode:"
        echo "   Test webhook: curl -X POST http://localhost:${PORT:-5000}/health"
        echo "   View target repos: curl http://localhost:${PORT:-5000}/repos"
    fi
    
else
    echo "❌ Health check failed - Service may not be running properly"
    echo "📋 Check logs for details:"
    echo "   Docker: docker logs pr-coverage-analyzer-$ENVIRONMENT"
    echo "   Local: tail -f logs/error.log"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
