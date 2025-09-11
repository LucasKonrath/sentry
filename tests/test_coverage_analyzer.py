"""
Tests for the coverage analyzer module.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from src.analyzers.coverage_analyzer import CoverageAnalyzer


class TestCoverageAnalyzer:
    """Test cases for CoverageAnalyzer."""
    
    def test_init(self, mock_config):
        """Test CoverageAnalyzer initialization."""
        analyzer = CoverageAnalyzer(mock_config)
        assert analyzer.config == mock_config
        assert analyzer.coverage_threshold == mock_config.coverage_threshold
    
    @patch('subprocess.run')
    @patch('builtins.open', new_callable=mock_open, read_data='{"totals": {"percent_covered": 75.5}}')
    @patch('pathlib.Path.exists')
    def test_analyze_coverage_success(self, mock_exists, mock_file, mock_subprocess, mock_config):
        """Test successful coverage analysis."""
        mock_exists.return_value = True
        mock_subprocess.return_value = Mock(returncode=0, stderr="")
        
        analyzer = CoverageAnalyzer(mock_config)
        changed_files = ["src/utils/helper.py", "src/main.py"]
        
        result = analyzer.analyze_coverage(changed_files)
        
        assert "overall_coverage" in result
        assert "file_coverage" in result
        assert "low_coverage_areas" in result
        assert isinstance(result["meets_threshold"], bool)
    
    def test_find_low_coverage_areas(self, mock_config):
        """Test finding areas with low coverage."""
        analyzer = CoverageAnalyzer(mock_config)
        
        coverage_report = {
            "files": {
                "src/low_coverage.py": {
                    "summary": {"percent_covered": 30.0},
                    "missing_lines": [5, 10, 15]
                },
                "src/good_coverage.py": {
                    "summary": {"percent_covered": 90.0},
                    "missing_lines": [20]
                }
            }
        }
        
        low_areas = analyzer._find_low_coverage_areas(coverage_report, 80)
        
        assert len(low_areas) == 1
        assert low_areas[0]["file"] == "src/low_coverage.py"
        assert low_areas[0]["current_coverage"] == 30.0
        assert low_areas[0]["priority"] == "high"
    
    def test_calculate_coverage_improvement(self, mock_config):
        """Test coverage improvement calculation."""
        analyzer = CoverageAnalyzer(mock_config)
        
        before_report = {"overall_coverage": 65.0}
        after_report = {"overall_coverage": 78.0}
        
        improvement = analyzer.calculate_coverage_improvement(before_report, after_report)
        
        assert improvement["before"] == 65.0
        assert improvement["after"] == 78.0
        assert improvement["improvement"] == 13.0
        assert improvement["improvement_percentage"] == pytest.approx(20.0, rel=1e-2)
        assert improvement["meets_minimum_increase"] == True  # > 5% threshold
