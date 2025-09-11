"""
Cobertura XML coverage format parser and analyzer.
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from defusedxml.ElementTree import parse as safe_parse

logger = logging.getLogger(__name__)


class CoberturaParser:
    """Parser for Cobertura XML coverage reports."""
    
    def __init__(self):
        self.supported_formats = ['.xml']
    
    def parse_coverage_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a Cobertura XML coverage file.
        
        Args:
            file_path: Path to the Cobertura XML file
            
        Returns:
            Dictionary containing parsed coverage data
        """
        try:
            if not Path(file_path).exists():
                logger.error(f"Coverage file not found: {file_path}")
                return {}
            
            # Parse XML safely
            tree = safe_parse(file_path)
            root = tree.getroot()
            
            if root.tag != 'coverage':
                logger.error(f"Invalid Cobertura format - root tag is '{root.tag}', expected 'coverage'")
                return {}
            
            # Extract overall metrics
            overall_coverage = self._extract_overall_coverage(root)
            
            # Extract per-package coverage
            packages_coverage = self._extract_packages_coverage(root)
            
            # Extract per-file coverage
            files_coverage = self._extract_files_coverage(root)
            
            return {
                'format': 'cobertura',
                'totals': overall_coverage,
                'packages': packages_coverage,
                'files': files_coverage,
                'timestamp': root.get('timestamp', ''),
                'version': root.get('version', ''),
                'source_paths': self._extract_source_paths(root)
            }
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error in {file_path}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing Cobertura file {file_path}: {str(e)}")
            return {}
    
    def _extract_overall_coverage(self, root: ET.Element) -> Dict[str, Any]:
        """Extract overall coverage metrics."""
        coverage_data = {
            'lines_valid': 0,
            'lines_covered': 0,
            'line_rate': 0.0,
            'branches_valid': 0,
            'branches_covered': 0,
            'branch_rate': 0.0,
            'percent_covered': 0.0
        }
        
        try:
            # Get attributes from root coverage element
            line_rate = float(root.get('line-rate', 0))
            branch_rate = float(root.get('branch-rate', 0))
            lines_covered = int(root.get('lines-covered', 0))
            lines_valid = int(root.get('lines-valid', 0))
            branches_covered = int(root.get('branches-covered', 0))
            branches_valid = int(root.get('branches-valid', 0))
            
            coverage_data.update({
                'lines_valid': lines_valid,
                'lines_covered': lines_covered,
                'line_rate': line_rate,
                'branches_valid': branches_valid,
                'branches_covered': branches_covered,
                'branch_rate': branch_rate,
                'percent_covered': line_rate * 100  # Convert to percentage
            })
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing overall coverage metrics: {str(e)}")
        
        return coverage_data
    
    def _extract_packages_coverage(self, root: ET.Element) -> Dict[str, Dict[str, Any]]:
        """Extract per-package coverage metrics."""
        packages = {}
        
        packages_elem = root.find('packages')
        if packages_elem is None:
            return packages
        
        for package_elem in packages_elem.findall('package'):
            package_name = package_elem.get('name', '')
            
            try:
                line_rate = float(package_elem.get('line-rate', 0))
                branch_rate = float(package_elem.get('branch-rate', 0))
                
                packages[package_name] = {
                    'line_rate': line_rate,
                    'branch_rate': branch_rate,
                    'percent_covered': line_rate * 100,
                    'classes': self._extract_classes_from_package(package_elem)
                }
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing package {package_name}: {str(e)}")
                continue
        
        return packages
    
    def _extract_files_coverage(self, root: ET.Element) -> Dict[str, Dict[str, Any]]:
        """Extract per-file coverage metrics with line details."""
        files = {}
        
        packages_elem = root.find('packages')
        if packages_elem is None:
            return files
        
        for package_elem in packages_elem.findall('package'):
            classes_elem = package_elem.find('classes')
            if classes_elem is None:
                continue
            
            for class_elem in classes_elem.findall('class'):
                filename = class_elem.get('filename', '')
                if not filename:
                    continue
                
                try:
                    line_rate = float(class_elem.get('line-rate', 0))
                    branch_rate = float(class_elem.get('branch-rate', 0))
                    
                    # Extract line-by-line coverage
                    lines_data = self._extract_lines_data(class_elem)
                    
                    files[filename] = {
                        'summary': {
                            'percent_covered': line_rate * 100,
                            'line_rate': line_rate,
                            'branch_rate': branch_rate
                        },
                        'missing_lines': lines_data['missing_lines'],
                        'covered_lines': lines_data['covered_lines'],
                        'partial_lines': lines_data['partial_lines'],
                        'line_details': lines_data['line_details']
                    }
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing file {filename}: {str(e)}")
                    continue
        
        return files
    
    def _extract_classes_from_package(self, package_elem: ET.Element) -> Dict[str, Dict[str, Any]]:
        """Extract class-level coverage from a package."""
        classes = {}
        
        classes_elem = package_elem.find('classes')
        if classes_elem is None:
            return classes
        
        for class_elem in classes_elem.findall('class'):
            class_name = class_elem.get('name', '')
            
            try:
                line_rate = float(class_elem.get('line-rate', 0))
                branch_rate = float(class_elem.get('branch-rate', 0))
                
                classes[class_name] = {
                    'filename': class_elem.get('filename', ''),
                    'line_rate': line_rate,
                    'branch_rate': branch_rate,
                    'percent_covered': line_rate * 100,
                    'methods': self._extract_methods_from_class(class_elem)
                }
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing class {class_name}: {str(e)}")
                continue
        
        return classes
    
    def _extract_methods_from_class(self, class_elem: ET.Element) -> Dict[str, Dict[str, Any]]:
        """Extract method-level coverage from a class."""
        methods = {}
        
        methods_elem = class_elem.find('methods')
        if methods_elem is None:
            return methods
        
        for method_elem in methods_elem.findall('method'):
            method_name = method_elem.get('name', '')
            
            try:
                line_rate = float(method_elem.get('line-rate', 0))
                branch_rate = float(method_elem.get('branch-rate', 0))
                
                methods[method_name] = {
                    'signature': method_elem.get('signature', ''),
                    'line_rate': line_rate,
                    'branch_rate': branch_rate,
                    'percent_covered': line_rate * 100
                }
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing method {method_name}: {str(e)}")
                continue
        
        return methods
    
    def _extract_lines_data(self, class_elem: ET.Element) -> Dict[str, Any]:
        """Extract detailed line coverage information."""
        lines_data = {
            'missing_lines': [],
            'covered_lines': [],
            'partial_lines': [],
            'line_details': {}
        }
        
        lines_elem = class_elem.find('lines')
        if lines_elem is None:
            return lines_data
        
        for line_elem in lines_elem.findall('line'):
            try:
                line_number = int(line_elem.get('number', 0))
                hits = int(line_elem.get('hits', 0))
                branch = line_elem.get('branch', 'false').lower() == 'true'
                condition_coverage = line_elem.get('condition-coverage', '')
                
                line_info = {
                    'hits': hits,
                    'branch': branch,
                    'condition_coverage': condition_coverage
                }
                
                lines_data['line_details'][line_number] = line_info
                
                if hits == 0:
                    lines_data['missing_lines'].append(line_number)
                elif branch and condition_coverage and '100%' not in condition_coverage:
                    lines_data['partial_lines'].append(line_number)
                else:
                    lines_data['covered_lines'].append(line_number)
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing line data: {str(e)}")
                continue
        
        return lines_data
    
    def _extract_source_paths(self, root: ET.Element) -> List[str]:
        """Extract source paths from the coverage report."""
        source_paths = []
        
        sources_elem = root.find('sources')
        if sources_elem is not None:
            for source_elem in sources_elem.findall('source'):
                path = source_elem.text
                if path:
                    source_paths.append(path.strip())
        
        return source_paths
    
    def convert_to_standard_format(self, cobertura_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Cobertura format to standard coverage format used by the analyzer.
        
        Args:
            cobertura_data: Parsed Cobertura data
            
        Returns:
            Standard format coverage data
        """
        if not cobertura_data or cobertura_data.get('format') != 'cobertura':
            return {}
        
        # Convert to standard format
        standard_format = {
            'overall_coverage': cobertura_data['totals']['percent_covered'],
            'file_coverage': {},
            'low_coverage_areas': [],
            'meets_threshold': False,  # Will be set by the analyzer
            'source_format': 'cobertura',
            'metadata': {
                'timestamp': cobertura_data.get('timestamp', ''),
                'version': cobertura_data.get('version', ''),
                'source_paths': cobertura_data.get('source_paths', [])
            }
        }
        
        # Convert file coverage
        for filename, file_data in cobertura_data.get('files', {}).items():
            standard_format['file_coverage'][filename] = {
                'summary': file_data['summary'],
                'missing_lines': file_data['missing_lines'],
                'covered_lines': file_data.get('covered_lines', []),
                'partial_lines': file_data.get('partial_lines', []),
                'line_details': file_data.get('line_details', {})
            }
        
        return standard_format
