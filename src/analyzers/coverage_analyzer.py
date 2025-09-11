"""
Coverage analysis module for extracting and analyzing test coverage data.
"""

import os
import subprocess
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """Analyzes test coverage for code changes in pull requests."""
    
    def __init__(self, config):
        self.config = config
        self.coverage_threshold = config.coverage_threshold
        
    def analyze_coverage(self, changed_files: List[str]) -> Dict[str, Any]:
        """
        Analyze test coverage for the given files.
        
        Args:
            changed_files: List of file paths that were changed in the PR
            
        Returns:
            Dictionary containing coverage analysis results
        """
        try:
            logger.info(f"Analyzing coverage for {len(changed_files)} files")
            
            # Run coverage analysis
            coverage_data = self._run_coverage_analysis(changed_files)
            
            # Parse coverage results
            coverage_report = self._parse_coverage_data(coverage_data)
            
            # Identify areas with low coverage
            low_coverage_areas = self._find_low_coverage_areas(
                coverage_report, self.coverage_threshold
            )
            
            return {
                "overall_coverage": coverage_report.get("totals", {}).get("percent_covered", 0),
                "file_coverage": coverage_report.get("files", {}),
                "low_coverage_areas": low_coverage_areas,
                "threshold": self.coverage_threshold,
                "meets_threshold": coverage_report.get("totals", {}).get("percent_covered", 0) >= self.coverage_threshold
            }
            
        except Exception as e:
            logger.error(f"Error analyzing coverage: {str(e)}")
            return {
                "error": str(e),
                "overall_coverage": 0,
                "file_coverage": {},
                "low_coverage_areas": [],
                "meets_threshold": False
            }
    
    def _run_coverage_analysis(self, changed_files: List[str]) -> Dict[str, Any]:
        """Run coverage analysis using pytest-cov."""
        try:
            # Create a temporary coverage config
            coverage_config = self._create_coverage_config(changed_files)
            
            # Run pytest with coverage
            cmd = [
                "python", "-m", "pytest",
                "--cov=src",
                "--cov-report=json:coverage.json",
                "--cov-report=term-missing",
                "tests/"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                logger.warning(f"Coverage analysis had issues: {result.stderr}")
            
            # Read the generated coverage JSON
            coverage_file = Path("coverage.json")
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning("No coverage.json file generated")
                return {}
                
        except Exception as e:
            logger.error(f"Error running coverage analysis: {str(e)}")
            return {}
    
    def _create_coverage_config(self, changed_files: List[str]) -> str:
        """Create coverage configuration for specific files."""
        config_content = f"""
[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__init__.py",
    "*/venv/*",
    "*/.venv/*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
show_missing = true
        """
        
        config_file = Path(".coveragerc")
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        return str(config_file)
    
    def _parse_coverage_data(self, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse coverage data into a structured format."""
        if not coverage_data:
            return {"totals": {"percent_covered": 0}, "files": {}}
        
        return coverage_data
    
    def _find_low_coverage_areas(self, coverage_report: Dict[str, Any], threshold: int) -> List[Dict[str, Any]]:
        """Find areas with coverage below the threshold."""
        low_coverage_areas = []
        
        files = coverage_report.get("files", {})
        for file_path, file_data in files.items():
            file_coverage = file_data.get("summary", {}).get("percent_covered", 0)
            
            if file_coverage < threshold:
                missing_lines = file_data.get("missing_lines", [])
                low_coverage_areas.append({
                    "file": file_path,
                    "current_coverage": file_coverage,
                    "missing_lines": missing_lines,
                    "priority": "high" if file_coverage < threshold * 0.5 else "medium"
                })
        
        # Sort by priority and coverage percentage
        low_coverage_areas.sort(
            key=lambda x: (x["priority"] == "high", -x["current_coverage"]), 
            reverse=True
        )
        
        return low_coverage_areas
    
    def calculate_coverage_improvement(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate coverage improvement between two reports."""
        before_coverage = before.get("overall_coverage", 0)
        after_coverage = after.get("overall_coverage", 0)
        
        improvement = after_coverage - before_coverage
        
        return {
            "before": before_coverage,
            "after": after_coverage,
            "improvement": improvement,
            "improvement_percentage": (improvement / before_coverage * 100) if before_coverage > 0 else 0,
            "meets_minimum_increase": improvement >= self.config.min_coverage_increase
        }
