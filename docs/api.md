# API Documentation

## Core Classes

### PRCoverageAnalyzer

Main orchestrator class for the entire workflow.

```python
class PRCoverageAnalyzer:
    def analyze_pr(self, repo_url: str, pr_number: int) -> dict:
        """
        Analyze a pull request and generate improved test coverage.
        
        Args:
            repo_url: GitHub repository URL
            pr_number: Pull request number
            
        Returns:
            Dictionary containing analysis results and generated PR info
        """
```

### CoverageAnalyzer

Analyzes test coverage for code changes.

```python
class CoverageAnalyzer:
    def analyze_coverage(self, changed_files: List[str]) -> Dict[str, Any]:
        """
        Analyze test coverage for the given files.
        
        Returns coverage report with overall coverage, file-specific coverage,
        and areas that need improvement.
        """
```

### CodeAnalyzer

Analyzes code structure to identify test opportunities.

```python
class CodeAnalyzer:
    def find_uncovered_areas(self, changed_files: List[str], 
                           coverage_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find specific code areas that lack test coverage.
        
        Returns detailed information about functions, methods, and classes
        that need test coverage.
        """
```

### TestGenerator

LLM-powered test generator.

```python
class TestGenerator:
    def generate_tests(self, uncovered_areas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate unit tests for uncovered code areas using LLM.
        
        Returns generated test code, file paths, and metadata.
        """
```

### PRManager

GitHub API integration for PR management.

```python
class PRManager:
    def get_pr_info(self, repo_url: str, pr_number: int) -> Dict[str, Any]:
        """Get detailed information about a pull request."""
        
    def create_test_pr(self, repo_url: str, original_pr_number: int, 
                      generated_tests: List[Dict[str, Any]], 
                      coverage_report: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pull request with generated tests."""
```

## Configuration

The `Config` class manages all configuration settings:

```python
class Config(BaseSettings):
    # GitHub Settings
    github_token: str
    default_branch: str = "main"
    pr_branch_prefix: str = "auto-tests/"
    
    # LLM Settings
    openai_api_key: str
    llm_model: str = "gpt-4"
    max_tokens: int = 4000
    temperature: float = 0.2
    
    # Coverage Settings
    coverage_threshold: int = 80
    min_coverage_increase: int = 5
```

## Data Structures

### Coverage Report
```python
{
    "overall_coverage": 65.5,
    "file_coverage": {
        "src/utils/helper.py": {
            "summary": {"percent_covered": 45.0},
            "missing_lines": [10, 15, 20, 25, 30]
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
```

### Uncovered Area
```python
{
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
    "priority": 85
}
```

### Generated Test
```python
{
    "source_function": {...},  # Uncovered area info
    "test_file_path": "tests/test_helper.py",
    "test_code": "class TestCalculateScore: ...",
    "test_class_name": "TestCalculateScore",
    "test_methods": ["test_basic_calculation", "test_edge_cases"],
    "imports": ["import pytest", "from unittest.mock import Mock"],
    "setup_code": "@pytest.fixture\ndef sample_data(): ...",
    "explanation": "Tests cover all execution paths and edge cases"
}
```
