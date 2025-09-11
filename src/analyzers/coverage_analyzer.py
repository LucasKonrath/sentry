"""
Coverage analysis module for extracting and analyzing test coverage data.
"""

import os
import subprocess
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .cobertura_parser import CoberturaParser

logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """Analyzes test coverage for code changes in pull requests."""
    
    def __init__(self, config):
        self.config = config
        self.coverage_threshold = config.coverage_threshold
        self.cobertura_parser = CoberturaParser()
        
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
            
            # First, try to find existing coverage reports
            existing_coverage = self._find_existing_coverage_reports()
            
            if existing_coverage:
                logger.info(f"Found existing coverage report: {existing_coverage}")
                coverage_report = self._parse_existing_coverage(existing_coverage)
            else:
                # Run coverage analysis
                coverage_data = self._run_coverage_analysis(changed_files)
                coverage_report = self._parse_coverage_data(coverage_data)
            
            # Identify areas with low coverage
            low_coverage_areas = self._find_low_coverage_areas(
                coverage_report, self.coverage_threshold
            )
            
            overall_coverage = coverage_report.get("overall_coverage", 0)
            if "totals" in coverage_report and "percent_covered" in coverage_report["totals"]:
                overall_coverage = coverage_report["totals"]["percent_covered"]
            
            return {
                "overall_coverage": overall_coverage,
                "file_coverage": coverage_report.get("file_coverage", coverage_report.get("files", {})),
                "low_coverage_areas": low_coverage_areas,
                "threshold": self.coverage_threshold,
                "meets_threshold": overall_coverage >= self.coverage_threshold,
                "source_format": coverage_report.get("source_format", "pytest"),
                "metadata": coverage_report.get("metadata", {})
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
        
        # Handle both old format ("files") and new standard format ("file_coverage")
        files = coverage_report.get("files", coverage_report.get("file_coverage", {}))
        
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
    
    def _find_existing_coverage_reports(self) -> Optional[str]:
        """Find existing coverage reports in common locations."""
        # Common coverage report locations and formats
        coverage_files = [
            # Cobertura XML
            'coverage.xml',
            'cobertura-coverage.xml', 
            'cobertura.xml',
            'target/site/cobertura/coverage.xml',  # Maven
            'build/reports/cobertura/coverage.xml',  # Gradle
            'coverage/cobertura-coverage.xml',
            
            # JSON formats
            'coverage.json',
            '.coverage.json',
            'coverage/coverage-final.json',  # Istanbul/NYC
            
            # LCOV format
            'coverage/lcov.info',
            'lcov.info',
            
            # JaCoCo
            'target/site/jacoco/jacoco.xml',
            'build/reports/jacoco/test/jacocoTestReport.xml',
            
            # .NET
            'coverage.cobertura.xml',
            'TestResults/coverage.cobertura.xml',
        ]
        
        current_dir = Path(os.getcwd())
        
        # Search in current directory and common subdirectories
        search_paths = [current_dir, current_dir / 'coverage', current_dir / 'target', current_dir / 'build']
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            for coverage_file in coverage_files:
                full_path = search_path / coverage_file
                if full_path.exists() and full_path.is_file():
                    logger.info(f"Found existing coverage report: {full_path}")
                    return str(full_path)
        
        return None
    
    def _parse_existing_coverage(self, coverage_file_path: str) -> Dict[str, Any]:
        """Parse existing coverage report based on file format."""
        file_path = Path(coverage_file_path)
        
        try:
            if file_path.suffix.lower() == '.xml':
                # Try Cobertura XML format
                logger.info("Parsing as Cobertura XML format")
                cobertura_data = self.cobertura_parser.parse_coverage_file(str(file_path))
                
                if cobertura_data:
                    return self.cobertura_parser.convert_to_standard_format(cobertura_data)
                else:
                    # Try JaCoCo or other XML formats
                    return self._parse_jacoco_xml(str(file_path))
            
            elif file_path.suffix.lower() == '.json':
                # Parse JSON coverage format
                logger.info("Parsing as JSON coverage format")
                return self._parse_json_coverage(str(file_path))
            
            elif file_path.name.endswith('lcov.info'):
                # Parse LCOV format
                logger.info("Parsing as LCOV format")
                return self._parse_lcov_coverage(str(file_path))
            
            else:
                logger.warning(f"Unknown coverage format: {file_path}")
                return {}
                
        except Exception as e:
            logger.error(f"Error parsing coverage file {coverage_file_path}: {str(e)}")
            return {}
    
    def _parse_jacoco_xml(self, file_path: str) -> Dict[str, Any]:
        """Parse JaCoCo XML format (placeholder - can be extended)."""
        logger.info("JaCoCo XML parsing not fully implemented yet")
        # This could be extended to parse JaCoCo format
        return {}
    
    def _parse_json_coverage(self, file_path: str) -> Dict[str, Any]:
        """Parse JSON coverage formats (Istanbul, pytest-cov JSON, etc.)."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Check if it's pytest-cov JSON format
            if 'totals' in data and 'files' in data:
                return {
                    'overall_coverage': data['totals'].get('percent_covered', 0),
                    'file_coverage': data['files'],
                    'source_format': 'pytest-json'
                }
            
            # Check if it's Istanbul/NYC format
            elif isinstance(data, dict) and any(key.endswith('.js') or key.endswith('.ts') for key in data.keys()):
                return self._convert_istanbul_format(data)
            
            else:
                logger.warning("Unknown JSON coverage format")
                return {}
                
        except Exception as e:
            logger.error(f"Error parsing JSON coverage: {str(e)}")
            return {}
    
    def _parse_lcov_coverage(self, file_path: str) -> Dict[str, Any]:
        """Parse LCOV format coverage (placeholder - can be extended)."""
        logger.info("LCOV parsing not implemented yet")
        # This could be extended to parse LCOV format
        return {}
    
    def _convert_istanbul_format(self, istanbul_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Istanbul/NYC JSON format to standard format."""
        file_coverage = {}
        total_lines = 0
        covered_lines = 0
        
        for file_path, file_data in istanbul_data.items():
            if not isinstance(file_data, dict):
                continue
                
            statements = file_data.get('s', {})
            statement_map = file_data.get('statementMap', {})
            
            file_missing_lines = []
            file_covered_lines = []
            
            for stmt_id, hit_count in statements.items():
                if stmt_id in statement_map:
                    line_num = statement_map[stmt_id].get('start', {}).get('line')
                    if line_num:
                        total_lines += 1
                        if hit_count > 0:
                            covered_lines += 1
                            file_covered_lines.append(line_num)
                        else:
                            file_missing_lines.append(line_num)
            
            if file_missing_lines or file_covered_lines:
                file_total = len(file_missing_lines) + len(file_covered_lines)
                file_coverage_pct = (len(file_covered_lines) / file_total * 100) if file_total > 0 else 0
                
                file_coverage[file_path] = {
                    'summary': {'percent_covered': file_coverage_pct},
                    'missing_lines': file_missing_lines,
                    'covered_lines': file_covered_lines
                }
        
        overall_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        return {
            'overall_coverage': overall_coverage,
            'file_coverage': file_coverage,
            'source_format': 'istanbul'
        }
