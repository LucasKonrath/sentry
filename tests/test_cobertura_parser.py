"""
Tests for the Cobertura parser module.
"""

import pytest
from src.analyzers.cobertura_parser import CoberturaParser


class TestCoberturaParser:
    """Test cases for CoberturaParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CoberturaParser()
    
    def test_supported_formats(self):
        """Test that the parser reports correct supported formats."""
        assert self.parser.supported_formats == ['.xml']
    
    def test_parse_valid_cobertura_xml(self):
        """Test parsing a valid Cobertura XML file."""
        result = self.parser.parse_coverage_file('examples/coverage.xml')
        
        # Verify the parsing worked correctly
        assert result['format'] == 'cobertura'
        assert 'totals' in result
        assert 'files' in result
        assert result['totals']['line_rate'] > 0.7
        assert result['totals']['branch_rate'] >= 0
    
    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        result = self.parser.parse_coverage_file('nonexistent.xml')
        assert result == {}
    
    def test_convert_to_standard_format(self):
        """Test conversion to standard format."""
        # Parse the sample file and convert it
        cobertura_data = self.parser.parse_coverage_file('examples/coverage.xml')
        result = self.parser.convert_to_standard_format(cobertura_data)
        
        # Check standard format structure
        assert 'overall_coverage' in result
        assert 'file_coverage' in result
        assert 'source_format' in result
        assert result['source_format'] == 'cobertura'
        
        # Check coverage values
        assert result['overall_coverage'] > 70
        
        # Check file coverage structure
        file_coverage = result['file_coverage']
        assert len(file_coverage) >= 2
