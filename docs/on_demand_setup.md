# On-Demand PR Coverage Analyzer Setup

## Overview

This guide shows how to set up the PR Coverage Analyzer to run automatically when PRs are created in targeted repositories using multiple deployment options.

## Option 1: GitHub Actions (Recommended)

### 1.1 Repository-Specific Setup

For each repository you want to monitor, add this workflow file:

**`.github/workflows/pr-coverage-analysis.yml`**

```yaml
name: Automatic PR Coverage Analysis

on:
  pull_request:
    types: [opened, synchronize, reopened]
    # Optionally filter by paths
    paths-ignore:
      - '*.md'
      - 'docs/**'
      - '.gitignore'

jobs:
  analyze-coverage:
    runs-on: ubuntu-latest
    if: github.event.pull_request.draft == false
    
    steps:
    - name: Checkout PR Coverage Analyzer
      uses: actions/checkout@v4
      with:
        repository: 'LucasKonrath/sentry'  # Your analyzer repo
        path: 'coverage-analyzer'
        token: ${{ secrets.COVERAGE_ANALYZER_TOKEN }}
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        cache: 'pip'
    
    - name: Install analyzer dependencies
      run: |
        cd coverage-analyzer
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run Coverage Analysis
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        COVERAGE_THRESHOLD: 80
        MIN_COVERAGE_INCREASE: 5
      run: |
        cd coverage-analyzer
        python -m src.main \
          --repo-url "${{ github.server_url }}/${{ github.repository }}" \
          --pr-number "${{ github.event.number }}"
    
    - name: Comment on PR
      if: always()
      uses: actions/github-script@v7
      with:
        script: |
          const { owner, repo } = context.repo;
          const issue_number = context.issue.number;
          
          github.rest.issues.createComment({
            owner,
            repo,
            issue_number,
            body: '🤖 PR Coverage Analysis has been triggered. Check for a new PR with generated tests!'
          });
```

### 1.2 Organization-Wide Setup

For organization-wide deployment, create a reusable workflow:

**`.github/workflows/reusable-coverage-analysis.yml`**

```yaml
name: Reusable Coverage Analysis

on:
  workflow_call:
    inputs:
      coverage-threshold:
        description: 'Minimum coverage threshold'
        required: false
        default: '80'
        type: string
      target-languages:
        description: 'Programming languages to analyze'
        required: false
        default: 'python,javascript,typescript'
        type: string
    secrets:
      OPENAI_API_KEY:
        required: true
      COVERAGE_ANALYZER_TOKEN:
        required: true

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      # ... (same steps as above but parameterized)
```

## Option 2: GitHub App (Enterprise Solution)

### 2.1 GitHub App Configuration

Create a GitHub App with these permissions:
- Repository permissions:
  - Contents: Read & Write
  - Pull requests: Read & Write
  - Issues: Write
- Subscribe to events:
  - Pull request

### 2.2 App Server Implementation

```python
# github_app_server.py
import os
import hmac
import hashlib
import subprocess
from flask import Flask, request, jsonify
from github import Github
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
WEBHOOK_SECRET = os.environ.get('GITHUB_WEBHOOK_SECRET')
GITHUB_APP_ID = os.environ.get('GITHUB_APP_ID')
PRIVATE_KEY_PATH = os.environ.get('GITHUB_PRIVATE_KEY_PATH')

# Target repositories (can be configured via environment or database)
TARGET_REPOS = os.environ.get('TARGET_REPOS', '').split(',')

def verify_signature(payload_body, signature_header):
    """Verify GitHub webhook signature."""
    if not signature_header:
        return False
    
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle GitHub webhook events."""
    signature = request.headers.get('X-Hub-Signature-256')
    
    if not verify_signature(request.data, signature):
        logger.warning('Invalid signature')
        return jsonify({'error': 'Invalid signature'}), 403
    
    payload = request.json
    event_type = request.headers.get('X-GitHub-Event')
    
    if event_type != 'pull_request':
        return jsonify({'message': 'Not a pull request event'}), 200
    
    action = payload.get('action')
    if action not in ['opened', 'synchronize', 'reopened']:
        return jsonify({'message': f'Action {action} not handled'}), 200
    
    # Check if repository is in target list
    repo_full_name = payload['repository']['full_name']
    if TARGET_REPOS and repo_full_name not in TARGET_REPOS:
        logger.info(f'Repository {repo_full_name} not in target list')
        return jsonify({'message': 'Repository not targeted'}), 200
    
    # Extract PR information
    pr_number = payload['number']
    repo_url = payload['repository']['html_url']
    pr_author = payload['pull_request']['user']['login']
    
    # Skip draft PRs
    if payload['pull_request'].get('draft', False):
        return jsonify({'message': 'Draft PR ignored'}), 200
    
    logger.info(f'Processing PR #{pr_number} in {repo_full_name}')
    
    try:
        # Run coverage analysis
        result = run_coverage_analysis(repo_url, pr_number)
        
        # Post comment on PR
        post_pr_comment(payload, result)
        
        return jsonify({
            'status': 'success',
            'message': f'Coverage analysis completed for PR #{pr_number}',
            'result': result
        })
        
    except Exception as e:
        logger.error(f'Error processing PR {pr_number}: {str(e)}')
        return jsonify({'error': str(e)}), 500

def run_coverage_analysis(repo_url, pr_number):
    """Run the coverage analysis for a PR."""
    env = os.environ.copy()
    env.update({
        'COVERAGE_THRESHOLD': '80',
        'MIN_COVERAGE_INCREASE': '5'
    })
    
    cmd = [
        'python', '-m', 'src.main',
        '--repo-url', repo_url,
        '--pr-number', str(pr_number)
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        cwd='/path/to/coverage-analyzer'
    )
    
    return {
        'exit_code': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr
    }

def post_pr_comment(payload, analysis_result):
    """Post a comment on the PR with analysis results."""
    # Implementation depends on your GitHub authentication method
    pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

## Option 3: Serverless Function (AWS Lambda/Vercel)

### 3.1 AWS Lambda Implementation

```python
# lambda_function.py
import json
import os
import subprocess
import boto3
from urllib.parse import urlencode

def lambda_handler(event, context):
    """AWS Lambda handler for GitHub webhooks."""
    
    # Parse the webhook payload
    if 'body' in event:
        payload = json.loads(event['body'])
    else:
        payload = event
    
    # Validate webhook (implement signature verification)
    
    # Check if it's a PR event we care about
    if not is_target_pr_event(payload):
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Event ignored'})
        }
    
    # Queue the analysis job
    sqs = boto3.client('sqs')
    queue_url = os.environ['ANALYSIS_QUEUE_URL']
    
    message = {
        'repo_url': payload['repository']['html_url'],
        'pr_number': payload['number'],
        'timestamp': payload['pull_request']['updated_at']
    }
    
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message)
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Analysis queued'})
    }

def is_target_pr_event(payload):
    """Check if this is a PR event we should process."""
    if payload.get('action') not in ['opened', 'synchronize', 'reopened']:
        return False
    
    if payload.get('pull_request', {}).get('draft', False):
        return False
    
    # Add more filtering logic as needed
    return True
```

### 3.2 Processing Function

```python
# analysis_processor.py
import json
import os
import subprocess
from src.main import PRCoverageAnalyzer

def process_analysis(event, context):
    """Process queued analysis jobs."""
    
    for record in event['Records']:
        message = json.loads(record['body'])
        
        repo_url = message['repo_url']
        pr_number = message['pr_number']
        
        try:
            # Run analysis
            analyzer = PRCoverageAnalyzer()
            result = analyzer.analyze_pr(repo_url, pr_number)
            
            # Log results
            print(f"Analysis complete for {repo_url} PR #{pr_number}: {result}")
            
        except Exception as e:
            print(f"Analysis failed for {repo_url} PR #{pr_number}: {str(e)}")
            # Optionally re-queue or send to DLQ
    
    return {'statusCode': 200}
```

## Option 4: Self-Hosted Runner

### 4.1 Docker Setup

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN useradd -m -u 1000 analyzer
USER analyzer

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
  CMD python -c "from src.main import PRCoverageAnalyzer; print('OK')"

EXPOSE 8000

CMD ["python", "-m", "src.webhook_server"]
```

### 4.2 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  pr-analyzer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
      - TARGET_REPOS=${TARGET_REPOS}
      - COVERAGE_THRESHOLD=80
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - pr-analyzer
    restart: unless-stopped
```

## Configuration Files

### Target Repository Configuration

```yaml
# config/target_repos.yml
repositories:
  - owner: myorg
    name: backend-api
    settings:
      coverage_threshold: 85
      languages: [python, javascript]
      exclude_paths: [docs/, scripts/]
      
  - owner: myorg
    name: frontend-app
    settings:
      coverage_threshold: 75
      languages: [typescript, javascript]
      exclude_paths: [public/, stories/]
      
  - owner: anotherorg
    name: microservice
    settings:
      coverage_threshold: 90
      languages: [java]
```

### Environment Configuration

```bash
# .env.production
GITHUB_TOKEN=ghp_your_token_here
OPENAI_API_KEY=sk-your_openai_key_here
WEBHOOK_SECRET=your_webhook_secret
TARGET_REPOS=myorg/backend-api,myorg/frontend-app,anotherorg/microservice

# Coverage settings
COVERAGE_THRESHOLD=80
MIN_COVERAGE_INCREASE=5

# Server settings
PORT=8000
LOG_LEVEL=INFO

# Optional: Database for tracking
DATABASE_URL=postgresql://user:pass@localhost/coverage_db
```

## Deployment Instructions

### Quick Setup (GitHub Actions)

1. **Add secrets to target repositories:**
   ```bash
   # In each target repo's Settings > Secrets
   OPENAI_API_KEY: your_openai_api_key
   COVERAGE_ANALYZER_TOKEN: github_token_with_repo_access
   ```

2. **Copy workflow file to target repos:**
   ```bash
   mkdir -p .github/workflows
   cp docs/github-actions-workflow.yml .github/workflows/pr-coverage-analysis.yml
   ```

3. **Customize settings in workflow file as needed**

### Self-Hosted Setup

1. **Clone and configure:**
   ```bash
   git clone https://github.com/LucasKonrath/sentry.git coverage-analyzer
   cd coverage-analyzer
   cp config/env.example .env
   # Edit .env with your settings
   ```

2. **Deploy with Docker:**
   ```bash
   docker-compose up -d
   ```

3. **Configure webhooks in target repositories:**
   - URL: `https://your-server.com/webhook`
   - Content type: `application/json`
   - Events: Pull requests
   - Secret: Your webhook secret

## Monitoring and Logging

The system includes comprehensive logging and monitoring capabilities to track analysis results and performance.

Choose the option that best fits your infrastructure and requirements!
