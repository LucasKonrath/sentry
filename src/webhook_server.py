"""
Webhook server for handling GitHub webhook events and triggering PR analysis.
"""

import os
import hmac
import hashlib
import json
import logging
from typing import Dict, Any, List
from flask import Flask, request, jsonify
from datetime import datetime
import yaml
from pathlib import Path

from .main import PRCoverageAnalyzer
from .utils.config import Config

app = Flask(__name__)
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Configuration
WEBHOOK_SECRET = os.environ.get('GITHUB_WEBHOOK_SECRET', '')
TARGET_REPOS_CONFIG = Path('config/target_repos.yml')

class WebhookServer:
    """GitHub webhook server for PR coverage analysis."""
    
    def __init__(self):
        self.config = Config()
        self.analyzer = PRCoverageAnalyzer()
        self.target_repos = self._load_target_repos()
    
    def _load_target_repos(self) -> Dict[str, Any]:
        """Load target repository configuration."""
        if TARGET_REPOS_CONFIG.exists():
            with open(TARGET_REPOS_CONFIG, 'r') as f:
                return yaml.safe_load(f)
        
        # Fallback to environment variable
        env_repos = os.environ.get('TARGET_REPOS', '')
        if env_repos:
            repos = {}
            for repo in env_repos.split(','):
                if '/' in repo:
                    owner, name = repo.strip().split('/', 1)
                    repos[repo.strip()] = {
                        'owner': owner,
                        'name': name,
                        'settings': {
                            'coverage_threshold': int(os.environ.get('COVERAGE_THRESHOLD', 80)),
                            'languages': ['python', 'javascript', 'typescript']
                        }
                    }
            return {'repositories': list(repos.values())}
        
        return {'repositories': []}
    
    def verify_signature(self, payload_body: bytes, signature_header: str) -> bool:
        """Verify GitHub webhook signature."""
        if not WEBHOOK_SECRET or not signature_header:
            logger.warning("No webhook secret configured or signature missing")
            return False
        
        expected_signature = hmac.new(
            WEBHOOK_SECRET.encode('utf-8'),
            payload_body,
            hashlib.sha256
        ).hexdigest()
        
        received_signature = signature_header.replace('sha256=', '')
        return hmac.compare_digest(expected_signature, received_signature)
    
    def is_target_repository(self, repo_full_name: str) -> Dict[str, Any]:
        """Check if repository is in target list and return its config."""
        for repo_config in self.target_repos.get('repositories', []):
            if isinstance(repo_config, str):
                if repo_config == repo_full_name:
                    return {'settings': {'coverage_threshold': 80}}
            elif isinstance(repo_config, dict):
                owner = repo_config.get('owner', '')
                name = repo_config.get('name', '')
                full_name = f"{owner}/{name}"
                if full_name == repo_full_name:
                    return repo_config
        
        return None
    
    def should_process_pr(self, payload: Dict[str, Any]) -> tuple[bool, str]:
        """Determine if PR should be processed."""
        action = payload.get('action')
        if action not in ['opened', 'synchronize', 'reopened']:
            return False, f"Action '{action}' not processed"
        
        pr_data = payload.get('pull_request', {})
        if pr_data.get('draft', False):
            return False, "Draft PR ignored"
        
        # Check if PR is from a fork (optional security measure)
        if pr_data.get('head', {}).get('repo', {}).get('fork', False):
            # You might want to be more careful with forks
            logger.info("PR is from a fork, processing with caution")
        
        return True, "PR approved for processing"
    
    def process_pull_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process a pull request webhook event."""
        try:
            # Extract PR information
            pr_number = payload['number']
            repo_data = payload['repository']
            repo_url = repo_data['html_url']
            repo_full_name = repo_data['full_name']
            pr_author = payload['pull_request']['user']['login']
            
            logger.info(f"Processing PR #{pr_number} from {pr_author} in {repo_full_name}")
            
            # Check if repository is targeted
            repo_config = self.is_target_repository(repo_full_name)
            if not repo_config:
                return {
                    'status': 'skipped',
                    'message': f'Repository {repo_full_name} not in target list'
                }
            
            # Check if PR should be processed
            should_process, reason = self.should_process_pr(payload)
            if not should_process:
                return {
                    'status': 'skipped',
                    'message': reason
                }
            
            # Override config with repo-specific settings
            repo_settings = repo_config.get('settings', {})
            original_threshold = self.config.coverage_threshold
            
            if 'coverage_threshold' in repo_settings:
                self.config.coverage_threshold = repo_settings['coverage_threshold']
            
            try:
                # Run the analysis
                result = self.analyzer.analyze_pr(repo_url, pr_number)
                
                # Add metadata
                result.update({
                    'repository': repo_full_name,
                    'pr_author': pr_author,
                    'processed_at': datetime.utcnow().isoformat(),
                    'repo_config': repo_settings
                })
                
                return result
                
            finally:
                # Restore original config
                self.config.coverage_threshold = original_threshold
                
        except Exception as e:
            logger.error(f"Error processing PR: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'success': False
            }

# Global webhook server instance
webhook_server = WebhookServer()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.1.0'
    })

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle GitHub webhook events."""
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not webhook_server.verify_signature(request.data, signature):
        logger.warning('Invalid webhook signature')
        return jsonify({'error': 'Invalid signature'}), 403
    
    # Check event type
    event_type = request.headers.get('X-GitHub-Event')
    if event_type != 'pull_request':
        return jsonify({'message': 'Not a pull request event'}), 200
    
    payload = request.json
    
    try:
        result = webhook_server.process_pull_request(payload)
        
        # Log the result
        if result.get('success', False):
            logger.info(f"Successfully processed PR: {result}")
        elif result.get('status') == 'skipped':
            logger.info(f"Skipped PR: {result['message']}")
        else:
            logger.error(f"Failed to process PR: {result}")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Webhook handler error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'success': False
        }), 500

@app.route('/repos', methods=['GET'])
def list_target_repos():
    """List configured target repositories."""
    return jsonify({
        'target_repositories': webhook_server.target_repos,
        'total_count': len(webhook_server.target_repos.get('repositories', []))
    })

@app.route('/trigger', methods=['POST'])
def manual_trigger():
    """Manually trigger analysis for a PR."""
    data = request.json
    
    required_fields = ['repo_url', 'pr_number']
    if not all(field in data for field in required_fields):
        return jsonify({
            'error': 'Missing required fields: repo_url, pr_number'
        }), 400
    
    try:
        result = webhook_server.analyzer.analyze_pr(
            data['repo_url'], 
            int(data['pr_number'])
        )
        
        result.update({
            'triggered_manually': True,
            'processed_at': datetime.utcnow().isoformat()
        })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Manual trigger error: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting webhook server on port {port}")
    logger.info(f"Target repositories: {len(webhook_server.target_repos.get('repositories', []))}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
