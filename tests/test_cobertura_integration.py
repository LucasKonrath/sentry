"""
Integration tests for Cobertura support in the coverage analyzer.
"""

import pytest
from unittest.mock import Mock
from src.analyzers.coverage_analyzer import CoverageAnalyzer
from src.analyzers.cobertura_parser import CoberturaParser


class TestCoberturaIntegration:
    """Integration tests for Cobertura support."""
    
    def test_cobertura_parser_with_sample_file(self):
        """Test Cobertura parser with the provided sample file."""
        parser = CoberturaParser()
        result = parser.parse_coverage_file('examples/coverage.xml')
        
        # Verify basic parsing worked
        assert result is not None
        assert result.get('format') == 'cobertura'
        assert 'totals' in result
        assert 'files' in result
        
        # Check overall coverage
        totals = result['totals']
        assert totals['percent_covered'] > 75  # Should be around 78.5%
        assert totals['line_rate'] > 0.75
        
        # Check file coverage
        files = result['files']
        assert len(files) >= 2  # Should have Calculator.java and StringUtils.java
        
        # Find a file with missing lines
        calculator_file = None
        for filename, file_data in files.items():
            if 'Calculator.java' in filename:
                calculator_file = file_data
                break
        
        assert calculator_file is not None
        assert 'missing_lines' in calculator_file
        assert len(calculator_file['missing_lines']) > 0
    
    def test_cobertura_conversion_to_standard_format(self):
        """Test conversion of Cobertura data to standard format."""
        parser = CoberturaParser()
        cobertura_data = parser.parse_coverage_file('examples/coverage.xml')
        
        # Convert to standard format
        standard_data = parser.convert_to_standard_format(cobertura_data)
        
        # Verify standard format structure
        assert 'overall_coverage' in standard_data
        assert 'file_coverage' in standard_data
        assert 'source_format' in standard_data
        assert standard_data['source_format'] == 'cobertura'
        
        # Check coverage values
        assert standard_data['overall_coverage'] > 75
        
        # Check file coverage structure
        file_coverage = standard_data['file_coverage']
        assert len(file_coverage) >= 2
        
        for filename, file_data in file_coverage.items():
            assert 'summary' in file_data
            assert 'missing_lines' in file_data
            assert 'percent_covered' in file_data['summary']
    
    def test_coverage_analyzer_with_cobertura(self):
        """Test that CoverageAnalyzer can use Cobertura data."""
        # Create a mock config
        mock_config = Mock()
        mock_config.coverage_threshold = 80
        mock_config.min_coverage_increase = 5
        
        analyzer = CoverageAnalyzer(mock_config)
        
        # Test that the analyzer can find and parse the sample file
        # We'll mock the file finding to point to our sample
        with pytest.MonkeyPatch().context() as m:
            m.setattr(analyzer, '_find_existing_coverage_reports', 
                     lambda: 'examples/coverage.xml')
            
            # Analyze coverage for some mock changed files
            result = analyzer.analyze_coverage(['src/Calculator.java'])
            
            # Verify the analyzer processed the Cobertura data
            assert 'overall_coverage' in result
            assert 'file_coverage' in result
            assert 'low_coverage_areas' in result
            assert 'source_format' in result
            assert result['source_format'] == 'cobertura'
            
            # Should find low coverage areas since threshold is 80% and we have files below that
            assert len(result['low_coverage_areas']) > 0
    
    def test_cobertura_missing_lines_extraction(self):
        """Test that missing lines are correctly extracted from Cobertura."""
        parser = CoberturaParser()
        result = parser.parse_coverage_file('examples/coverage.xml')
        
        # Find StringUtils file which has more missing coverage
        string_utils_file = None
        for filename, file_data in result['files'].items():
            if 'StringUtils.java' in filename:
                string_utils_file = file_data
                break
        
        assert string_utils_file is not None
        
        # Check that we have missing lines (lines with hits=0)
        missing_lines = string_utils_file['missing_lines']
        assert len(missing_lines) > 0
        
        # Check that we have line details
        line_details = string_utils_file.get('line_details', {})
        assert len(line_details) > 0
        
        # Verify missing lines have 0 hits
        for line_num in missing_lines:
            if line_num in line_details:
                assert line_details[line_num]['hits'] == 0
    
    def test_cobertura_branch_coverage_detection(self):
        """Test that branch coverage is correctly detected."""
        parser = CoberturaParser()
        result = parser.parse_coverage_file('examples/coverage.xml')
        
        # Look for partial lines (branch lines with incomplete coverage)
        found_partial = False
        for filename, file_data in result['files'].items():
            if 'partial_lines' in file_data and len(file_data['partial_lines']) > 0:
                found_partial = True
                
                # Check that partial lines have condition coverage info
                line_details = file_data.get('line_details', {})
                for line_num in file_data['partial_lines']:
                    if line_num in line_details:
                        line_info = line_details[line_num]
                        assert line_info.get('branch', False) == True
                        assert 'condition_coverage' in line_info
                        assert line_info['condition_coverage'] != '100%'
                break
        
        assert found_partial, "Should find at least one partial branch coverage line"
