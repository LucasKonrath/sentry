# GitHub Actions Workflow for PR Coverage Analyzer

This workflow can be set up to automatically analyze PRs when they're opened or updated.

## Setup Instructions

1. Create `.github/workflows/pr-coverage-analyzer.yml`:

```yaml
name: PR Coverage Analysis

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  analyze-coverage:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run coverage analysis
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        python -m src.main --repo-url "${{ github.repository }}" --pr-number "${{ github.event.number }}"
```

## Required Secrets

Add these secrets to your repository settings:

- `OPENAI_API_KEY`: Your OpenAI API key for LLM test generation
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

## Webhook Integration

For real-time PR analysis, you can set up a webhook that triggers the analyzer:

```python
# webhook_handler.py
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.json
    
    if payload.get('action') in ['opened', 'synchronize']:
        pr_number = payload['number']
        repo_url = payload['repository']['html_url']
        
        # Run the analyzer
        result = subprocess.run([
            'python', '-m', 'src.main',
            '--repo-url', repo_url,
            '--pr-number', str(pr_number)
        ], capture_output=True, text=True)
        
        return jsonify({'status': 'success', 'output': result.stdout})
    
    return jsonify({'status': 'ignored'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```
