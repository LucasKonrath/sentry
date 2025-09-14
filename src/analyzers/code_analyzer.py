"""
Code analysis module for understanding code structure and identifying test opportunities.
"""

import ast
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyzes code structure to identify areas that need test coverage."""
    
    def __init__(self, config):
        self.config = config
        self.supported_extensions = {
            '.py': self._analyze_python_file,
            '.js': self._analyze_javascript_file,
            '.ts': self._analyze_typescript_file,
            '.java': self._analyze_java_file
        }
    
    def find_uncovered_areas(self, changed_files: List[str], coverage_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find specific code areas that lack test coverage.
        
        Args:
            changed_files: List of file paths that were changed
            coverage_report: Coverage analysis results
            
        Returns:
            List of uncovered code areas with details for test generation
        """
        uncovered_areas = []
        low_coverage_files = coverage_report.get("low_coverage_areas", [])
        
        # Only analyze files inside the target project source directory
        project_src_dir = os.path.abspath("src")
        for coverage_area in low_coverage_files:
            file_path = os.path.abspath(coverage_area["file"])
            # Skip files not inside the project src directory
            if not file_path.startswith(project_src_dir):
                logger.info(f"Skipping non-project file: {file_path}")
                continue
            missing_lines = coverage_area.get("missing_lines", [])

            # Analyze the file structure
            file_analysis = self._analyze_file_structure(file_path)

            if file_analysis:
                # Find specific functions/classes that need tests
                uncovered_functions = self._find_uncovered_functions(
                    file_analysis, missing_lines
                )

                for func_info in uncovered_functions:
                    uncovered_areas.append({
                        "file_path": file_path,
                        "function_name": func_info["name"],
                        "function_type": func_info["type"],  # function, method, class
                        "line_start": func_info["line_start"],
                        "line_end": func_info["line_end"],
                        "signature": func_info["signature"],
                        "docstring": func_info.get("docstring", ""),
                        "complexity": func_info.get("complexity", "medium"),
                        "dependencies": func_info.get("dependencies", []),
                        "missing_lines": [
                            line for line in missing_lines 
                            if func_info["line_start"] <= line <= func_info["line_end"]
                        ],
                        "priority": self._calculate_priority(func_info, coverage_area)
                    })
        
        # Sort by priority
        uncovered_areas.sort(key=lambda x: x["priority"], reverse=True)
        
        return uncovered_areas
    
    def _analyze_file_structure(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Analyze the structure of a code file, resolving to absolute path."""
        try:
            # Always resolve to absolute path
            abs_file_path = os.path.abspath(file_path)
            file_ext = Path(abs_file_path).suffix
            if file_ext not in self.supported_extensions:
                logger.warning(f"Unsupported file type: {file_ext}")
                return None

            if not os.path.exists(abs_file_path):
                logger.error(f"File does not exist: {abs_file_path}")
                return None

            analyzer = self.supported_extensions[file_ext]
            return analyzer(abs_file_path)

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            return None
    
    def _analyze_python_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze Python file structure using AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "type": "method" if self._is_method(node, tree) else "function",
                        "line_start": node.lineno,
                        "line_end": node.end_lineno or node.lineno,
                        "signature": self._get_function_signature(node),
                        "docstring": ast.get_docstring(node) or "",
                        "complexity": self._calculate_complexity(node),
                        "dependencies": self._find_function_dependencies(node),
                        "is_private": node.name.startswith('_'),
                        "has_decorators": len(node.decorator_list) > 0,
                        "args": [arg.arg for arg in node.args.args]
                    }
                    functions.append(func_info)
                
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "type": "class",
                        "line_start": node.lineno,
                        "line_end": node.end_lineno or node.lineno,
                        "docstring": ast.get_docstring(node) or "",
                        "methods": [],
                        "has_init": any(
                            isinstance(n, ast.FunctionDef) and n.name == "__init__" 
                            for n in node.body
                        )
                    }
                    classes.append(class_info)
            
            return {
                "language": "python",
                "functions": functions,
                "classes": classes,
                "imports": self._extract_imports(tree),
                "source_code": source_code
            }
            
        except Exception as e:
            logger.error(f"Error parsing Python file {file_path}: {str(e)}")
            return {}
    
    def _analyze_javascript_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze JavaScript file structure (basic implementation)."""
        # This would need a proper JavaScript parser like esprima
        # For now, return basic structure
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Basic regex-based parsing (would be better with proper AST)
            import re
            
            functions = []
            function_pattern = r'(?:function\s+(\w+)|(\w+)\s*[=:]\s*(?:function|\([^)]*\)\s*=>))'
            
            for match in re.finditer(function_pattern, source_code):
                func_name = match.group(1) or match.group(2)
                line_num = source_code[:match.start()].count('\n') + 1
                
                functions.append({
                    "name": func_name,
                    "type": "function",
                    "line_start": line_num,
                    "line_end": line_num + 10,  # Approximation
                    "signature": f"function {func_name}(...)",
                    "complexity": "medium"
                })
            
            return {
                "language": "javascript",
                "functions": functions,
                "classes": [],
                "source_code": source_code
            }
            
        except Exception as e:
            logger.error(f"Error parsing JavaScript file {file_path}: {str(e)}")
            return {}
    
    def _analyze_typescript_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze TypeScript file structure."""
        # Similar to JavaScript but with type information
        return self._analyze_javascript_file(file_path)
    
    def _analyze_java_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze Java file structure (basic implementation)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Basic Java method detection
            import re
            
            methods = []
            method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\([^)]*\)\s*{'
            
            for match in re.finditer(method_pattern, source_code):
                method_name = match.group(1)
                line_num = source_code[:match.start()].count('\n') + 1
                
                methods.append({
                    "name": method_name,
                    "type": "method",
                    "line_start": line_num,
                    "line_end": line_num + 15,  # Approximation
                    "signature": f"public {method_name}(...)",
                    "complexity": "medium"
                })
            
            return {
                "language": "java",
                "functions": methods,
                "classes": [],
                "source_code": source_code
            }
            
        except Exception as e:
            logger.error(f"Error parsing Java file {file_path}: {str(e)}")
            return {}
    
    def _find_uncovered_functions(self, file_analysis: Dict[str, Any], missing_lines: List[int]) -> List[Dict[str, Any]]:
        """Find functions that have missing coverage."""
        uncovered_functions = []
        
        functions = file_analysis.get("functions", [])
        
        for func in functions:
            func_lines = set(range(func["line_start"], func["line_end"] + 1))
            missing_lines_set = set(missing_lines)
            
            # Check if this function has any missing coverage
            if func_lines.intersection(missing_lines_set):
                # Calculate what percentage of the function is uncovered
                uncovered_lines = len(func_lines.intersection(missing_lines_set))
                total_lines = len(func_lines)
                uncovered_percentage = (uncovered_lines / total_lines) * 100
                
                func["uncovered_percentage"] = uncovered_percentage
                uncovered_functions.append(func)
        
        return uncovered_functions
    
    def _is_method(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
        """Check if a function is a method (inside a class)."""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                if node in parent.body:
                    return True
        return False
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature from AST node."""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        
        return f"def {node.name}({', '.join(args)})"
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> str:
        """Calculate cyclomatic complexity (simplified)."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        if complexity <= 3:
            return "low"
        elif complexity <= 7:
            return "medium"
        else:
            return "high"
    
    def _find_function_dependencies(self, node: ast.FunctionDef) -> List[str]:
        """Find external dependencies used in the function."""
        dependencies = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                dependencies.add(child.id)
        
        # Filter out built-ins and arguments
        arg_names = {arg.arg for arg in node.args.args}
        builtin_names = set(dir(__builtins__))
        
        return list(dependencies - arg_names - builtin_names)
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements from the AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        
        return imports
    
    def _calculate_priority(self, func_info: Dict[str, Any], coverage_area: Dict[str, Any]) -> int:
        """Calculate priority score for test generation."""
        priority = 0
        
        # Base priority on coverage percentage
        uncovered_pct = func_info.get("uncovered_percentage", 0)
        priority += int(uncovered_pct)
        
        # Higher priority for public functions
        if not func_info.get("is_private", False):
            priority += 20
        
        # Higher priority for complex functions
        complexity = func_info.get("complexity", "medium")
        if complexity == "high":
            priority += 30
        elif complexity == "medium":
            priority += 15
        
        # Higher priority for functions with many dependencies
        deps_count = len(func_info.get("dependencies", []))
        priority += min(deps_count * 5, 25)
        
        return priority
