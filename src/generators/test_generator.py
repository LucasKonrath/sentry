"""
LLM-powered test generator for creating unit tests to improve code coverage.
Supports multiple LLM providers: OpenAI and Claude.
"""

import logging
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)


class TestGenerator:
    """Generates unit tests using LLM to improve code coverage."""
    
    def __init__(self, config):
        self.config = config
        self.provider = config.llm_provider.lower()
        self.model = config.llm_model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
        
        # Initialize provider-specific clients
        self.openai_client = None
        self.anthropic_client = None
        
        if self.provider == "openai" and config.openai_api_key:
            import openai
            self.openai_client = openai.OpenAI(api_key=config.openai_api_key)
        elif self.provider == "claude" and config.anthropic_api_key:
            import anthropic
            self.anthropic_client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        else:
            logger.warning(f"No valid API key found for provider: {self.provider}")
        
        logger.info(f"TestGenerator initialized with provider: {self.provider}, model: {self.model}")
    
    def _is_client_configured(self) -> bool:
        """Check if the appropriate LLM client is configured."""
        if self.provider == "openai":
            return self.openai_client is not None
        elif self.provider == "claude":
            return self.anthropic_client is not None
        return False
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the configured LLM provider."""
        try:
            if self.provider == "openai" and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                return response.choices[0].message.content
                
            elif self.provider == "claude" and self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return response.content[0].text
                
            else:
                raise ValueError(f"No configured client for provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"LLM API call failed: {str(e)}")
            raise
    
    def generate_tests(self, uncovered_areas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate unit tests for uncovered code areas.
        
        Args:
            uncovered_areas: List of code areas that need test coverage
            
        Returns:
            List of generated test information and code
        """
        if not self._is_client_configured():
            logger.error(f"LLM client not configured for provider: {self.provider}")
            return []
            
        generated_tests = []
        
        for area in uncovered_areas:
            try:
                logger.info(f"Generating test for {area['function_name']} in {area['file_path']}")
                
                test_info = self._generate_test_for_function(area)
                
                if test_info:
                    generated_tests.append({
                        "source_function": area,
                        "test_file_path": test_info["test_file_path"],
                        "test_code": test_info["test_code"],
                        "test_class_name": test_info["test_class_name"],
                        "test_methods": test_info["test_methods"],
                        "imports": test_info.get("imports", []),
                        "setup_code": test_info.get("setup_code", ""),
                        "explanation": test_info.get("explanation", "")
                    })
                
            except Exception as e:
                logger.error(f"Error generating test for {area['function_name']}: {str(e)}")
                continue
        
        return generated_tests
    
    def _generate_test_for_function(self, function_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a test for a specific function."""
        try:
            # Read the source code context
            source_code = self._get_source_code_context(function_info)
            
            # Create the prompt for test generation
            prompt = self._create_test_generation_prompt(function_info, source_code)
            
            # Call LLM to generate test
            system_prompt = self._get_system_prompt(function_info.get("language", "python"))
            test_content = self._call_llm(system_prompt, prompt)
            
            return self._parse_test_response(test_content, function_info)
            
        except Exception as e:
            logger.error(f"Error in LLM test generation: {str(e)}")
            return None
    
    def _get_source_code_context(self, function_info: Dict[str, Any]) -> str:
        """Get source code context around the function."""
        try:
            file_path = function_info["file_path"]
            line_start = max(1, function_info["line_start"] - 5)  # Add some context
            line_end = function_info["line_end"] + 5
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            context_lines = lines[line_start-1:line_end]
            return ''.join(context_lines)
            
        except Exception as e:
            logger.error(f"Error reading source context: {str(e)}")
            return ""
    
    def _create_test_generation_prompt(self, function_info: Dict[str, Any], source_code: str) -> str:
        """Create a detailed prompt for test generation."""
        
        language = "Python"  # Default to Python, extend for other languages
        
        prompt = f"""
I need you to generate comprehensive unit tests for the following {language} function.

**Function Information:**
- Name: {function_info['function_name']}
- Type: {function_info['function_type']}
- File: {function_info['file_path']}
- Signature: {function_info['signature']}
- Complexity: {function_info['complexity']}
- Missing coverage lines: {function_info['missing_lines']}

**Function Documentation:**
{function_info.get('docstring', 'No docstring available')}

**Source Code:**
```{language.lower()}
{source_code}
```

**Requirements:**
1. Generate comprehensive unit tests that cover ALL the missing lines: {function_info['missing_lines']}
2. Include tests for edge cases, error conditions, and normal flow
3. Use appropriate mocking for external dependencies: {function_info.get('dependencies', [])}
4. Follow {language} testing best practices ({self._get_testing_framework(language)})
5. Include setup and teardown if needed
6. Add clear, descriptive test method names
7. Include proper documentation/comments for test methods

**Test Coverage Goals:**
- Test all execution paths
- Test boundary conditions
- Test error handling
- Test with different input types
- Mock external dependencies appropriately

Please provide the complete test file content with:
- Proper imports
- Test class definition
- All necessary test methods
- Setup/teardown methods if needed
- Clear assertions

Format your response as a JSON object with:
{{
    "test_file_path": "path/to/test_file.py",
    "test_code": "complete test file content",
    "test_class_name": "TestClassName",
    "test_methods": ["method1", "method2", ...],
    "imports": ["import1", "import2", ...],
    "setup_code": "any setup code needed",
    "explanation": "brief explanation of the test strategy"
}}
"""
        return prompt
    
    def _get_testing_framework(self, language: str) -> str:
        """Get the appropriate testing framework for the language."""
        frameworks = {
            "python": "pytest with unittest.mock",
            "java": "JUnit 5 with Mockito",
            "javascript": "Jest or Mocha",
            "typescript": "Jest with TypeScript"
        }
        return frameworks.get(language.lower(), f"{language} testing framework")
    
    def _get_system_prompt(self, language: str) -> str:
        """Get system prompt for test generation."""
        
        if language.lower() == "python":
            return """
You are an expert Python developer and test engineer. Your task is to generate high-quality, comprehensive unit tests that will improve code coverage for the given function.

Key principles:
1. Write tests that are maintainable and readable
2. Use pytest framework and best practices
3. Mock external dependencies appropriately using unittest.mock
4. Cover edge cases and error conditions
5. Use descriptive test names that explain what is being tested
6. Include proper assertions with clear error messages
7. Follow AAA pattern (Arrange, Act, Assert)
8. Generate tests that will actually execute the missing lines of code

Always return valid JSON format as requested.
"""
        elif language.lower() == "java":
            return """
You are an expert Java developer and test engineer. Your task is to generate high-quality, comprehensive unit tests using JUnit 5 that will improve code coverage for the given function.

Key principles:
1. Use JUnit 5 framework (@Test, @BeforeEach, @AfterEach, etc.)
2. Use Mockito for mocking dependencies when needed
3. Follow Java naming conventions (camelCase for methods)
4. Use proper assertions (assertEquals, assertTrue, assertThrows, etc.)
5. Cover edge cases, error conditions, and normal flow
6. Include setup (@BeforeEach) and cleanup (@AfterEach) methods if needed
7. Use descriptive test method names that explain what is being tested
8. Generate tests that will actually execute the missing lines of code
9. Use proper Java imports (org.junit.jupiter.api.*, org.mockito.*, etc.)
10. Create proper test class structure with appropriate access modifiers

Always return valid JSON format as requested.
"""
        else:
            return f"""
You are an expert {language} developer and test engineer. Generate comprehensive unit tests for the given function following {language} testing best practices and appropriate testing frameworks.

Focus on covering all the specified missing lines and creating robust, maintainable tests.

Always return valid JSON format as requested.
"""
    
    def _parse_test_response(self, response_content: str, function_info: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the LLM response into structured test information."""
        try:
            # Try to extract JSON from the response
            # Sometimes LLM wraps JSON in markdown code blocks
            content = response_content.strip()
            
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            if content.endswith('```'):
                content = content[:-3]  # Remove ```
            
            # Fix common JSON issues
            import re
            
            # Fix missing colon after field names (specific Claude issue)
            content = re.sub(r'("test_code")(\s*")', r'\1:\2', content)
            content = re.sub(r'("test_file_path")(\s*")', r'\1:\2', content)
            content = re.sub(r'("test_class_name")(\s*")', r'\1:\2', content)
            content = re.sub(r'("imports")(\s*\[)', r'\1:\2', content)
            
            # Fix triple-quoted strings for JSON compatibility
            # This handles the specific case where Claude generates: "test_code": """code here"""
            def fix_triple_quotes(match):
                # Extract the content inside triple quotes
                raw_content = match.group(1)
                # Properly escape it for JSON
                return json.dumps(raw_content)
            
            content = re.sub(r':\s*"""\s*(.*?)\s*"""', fix_triple_quotes, content, flags=re.DOTALL)
            
            # Fix trailing commas (common LLM issue)
            content = re.sub(r',\s*}', '}', content)
            content = re.sub(r',\s*]', ']', content)
            
            # Fix single quotes to double quotes (but be careful not to break strings)
            content = re.sub(r"'([^']*)':", r'"\1":', content)
            
            # Try to clean up any remaining formatting issues
            content = content.strip()
            
            logger.debug(f"Cleaned JSON content: {content[:200]}...")
            
            # Parse JSON
            test_data = json.loads(content)
            
            # Validate and set defaults
            file_path = function_info["file_path"]
            test_file_name = f"test_{file_path.split('/')[-1]}"
            test_dir = file_path.replace("src/", "tests/").rsplit("/", 1)[0]
            
            return {
                "test_file_path": f"{test_dir}/{test_file_name}",
                "test_code": test_data.get("test_code", ""),
                "test_class_name": test_data.get("test_class_name", f"Test{function_info['function_name'].title()}"),
                "test_methods": test_data.get("test_methods", []),
                "imports": test_data.get("imports", []),
                "setup_code": test_data.get("setup_code", ""),
                "explanation": test_data.get("explanation", "")
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
            logger.error(f"Problematic JSON content: {content[:500]}...")
            # Fallback: try to extract code between triple backticks
            return self._fallback_parse_response(response_content, function_info)
        
        except Exception as e:
            logger.error(f"Error parsing test response: {str(e)}")
            return None
    
    def _fallback_parse_response(self, response_content: str, function_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback parsing when JSON parsing fails."""
        import re
        
        # Detect language from function info
        language = function_info.get("language", "python").lower()
        
        # Try to extract code from markdown code blocks for various languages
        language_patterns = {
            "python": r'```python\n(.*?)\n```',
            "java": r'```java\n(.*?)\n```',
            "javascript": r'```(javascript|js)\n(.*?)\n```',
            "typescript": r'```(typescript|ts)\n(.*?)\n```',
        }
        
        # Try language-specific pattern first
        if language in language_patterns:
            code_blocks = re.findall(language_patterns[language], response_content, re.DOTALL)
        else:
            # Fallback to generic code block
            code_blocks = re.findall(r'```\w*\n(.*?)\n```', response_content, re.DOTALL)
        
        if code_blocks:
            # Handle tuple results from patterns with groups
            if isinstance(code_blocks[0], tuple):
                test_code = code_blocks[0][-1]  # Get the last group (the actual code)
            else:
                test_code = code_blocks[0]
            
            # Language-specific parsing
            if language == "java":
                # Extract class name for Java
                class_match = re.search(r'class\s+(\w+)', test_code)
                class_name = class_match.group(1) if class_match else f"Test{function_info['function_name'].title()}"
                
                # Extract method names for Java
                method_matches = re.findall(r'@Test\s+public\s+void\s+(\w+)', test_code)
            else:
                # Python and other languages
                class_match = re.search(r'class\s+(\w+)', test_code)
                class_name = class_match.group(1) if class_match else f"Test{function_info['function_name'].title()}"
                
                # Extract method names for Python
                method_matches = re.findall(r'def\s+(test_\w+)', test_code)
            
            file_path = function_info["file_path"]
            test_file_name = f"test_{file_path.split('/')[-1]}"
            test_dir = file_path.replace("src/", "tests/").rsplit("/", 1)[0]
            
            return {
                "test_file_path": f"{test_dir}/{test_file_name}",
                "test_code": test_code,
                "test_class_name": class_name,
                "test_methods": method_matches,
                "imports": [],
                "setup_code": "",
                "explanation": "Generated using fallback parsing"
            }
        
        return None
    
    def validate_generated_test(self, test_info: Dict[str, Any]) -> bool:
        """Validate that the generated test is syntactically correct."""
        try:
            # Try to compile the test code
            compile(test_info["test_code"], "<string>", "exec")
            return True
        except SyntaxError as e:
            logger.error(f"Generated test has syntax error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error validating test: {str(e)}")
            return False
