"""
Test configuration and fixtures.
"""

import pytest
import os
from unittest.mock import Mock, patch
from src.utils.config import Config


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return Mock(spec=Config, **{
        'github_token': 'mock_token',
        'openai_api_key': 'mock_api_key',
        'coverage_threshold': 80,
        'min_coverage_increase': 5,
        'llm_model': 'gpt-4',
        'max_tokens': 4000,
        'temperature': 0.2,
        'pr_branch_prefix': 'auto-tests/',
        'pr_title_prefix': '[Auto] Add unit tests to improve coverage',
        'default_branch': 'main',
        'supported_languages': ['python', 'javascript', 'typescript', 'java'],
        'exclude_patterns': ['*.pyc', '__pycache__', 'node_modules', '*.git']
    })


@pytest.fixture
def sample_pr_info():
    """Sample PR information for testing."""
    return {
        "number": 123,
        "title": "Add new feature",
        "state": "open",
        "base_branch": "main",
        "head_branch": "feature-branch",
        "author": "developer",
        "url": "https://github.com/owner/repo/pull/123",
        "additions": 150,
        "deletions": 25,
        "changed_files": 5,
        "commits": 3
    }


@pytest.fixture
def sample_coverage_report():
    """Sample coverage report for testing."""
    return {
        "overall_coverage": 65.5,
        "file_coverage": {
            "src/utils/helper.py": {
                "summary": {"percent_covered": 45.0},
                "missing_lines": [10, 15, 20, 25, 30]
            },
            "src/analyzers/processor.py": {
                "summary": {"percent_covered": 70.0},
                "missing_lines": [5, 12, 18]
            }
        },
        "low_coverage_areas": [
            {
                "file": "src/utils/helper.py",
                "current_coverage": 45.0,
                "missing_lines": [10, 15, 20, 25, 30],
                "priority": "high"
            }
        ],
        "threshold": 80,
        "meets_threshold": False
    }


@pytest.fixture
def sample_function_info():
    """Sample function information for testing."""
    return {
        "file_path": "src/utils/helper.py",
        "function_name": "calculate_score",
        "function_type": "function",
        "line_start": 10,
        "line_end": 25,
        "signature": "def calculate_score(data, weights)",
        "docstring": "Calculate weighted score from data.",
        "complexity": "medium",
        "dependencies": ["numpy", "pandas"],
        "missing_lines": [15, 20, 22],
        "priority": 85,
        "uncovered_percentage": 40.0
    }
