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

Please provide the complete test file content as a properly formatted JSON response.

CRITICAL JSON FORMATTING REQUIREMENTS:
- Return ONLY a valid JSON object - no markdown, no code blocks, no extra text
- Use proper JSON escaping for the test_code field (\\n for newlines, \\" for quotes)
- Include the complete test class with all methods and imports
- Do NOT use triple quotes or markdown formatting

Required JSON structure:
{{
    "test_file_path": "src/test/java/YourTestClass.java",
    "test_code": "package com.example;\\n\\nimport org.junit.jupiter.api.Test;\\n\\npublic class YourTestClass {{\\n    @Test\\n    void testMethod() {{\\n        // your test code\\n    }}\\n}}",
    "test_class_name": "YourTestClass",
    "explanation": "Brief explanation of what this test covers"
}}

IMPORTANT: The test_code field must contain the complete, valid Java test class as a single properly escaped JSON string.
"""
        return prompt
    
    def _extract_class_name(self, code: str) -> str:
        """Extract class name from Java code."""
        import re
        match = re.search(r'class\s+(\w+)', code)
        return match.group(1) if match else "TestClass"
    
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

CRITICAL: You must return a valid JSON object with this EXACT structure:
{
    "test_file_path": "src/test/java/YourTestClass.java",
    "test_code": "your complete Java test code here - properly escaped for JSON",
    "test_class_name": "YourTestClass",
    "explanation": "Brief explanation of the test"
}

IMPORTANT JSON FORMATTING RULES:
- Use double quotes for all strings
- Escape all quotes inside the test_code string with \"
- Escape all newlines inside the test_code string with \\n
- Do NOT use triple quotes or markdown code blocks
- The test_code field must contain the complete Java test class as a single escaped string
- Ensure the JSON is valid and parseable

Example format:
{
    "test_file_path": "src/test/java/ExampleTest.java",
    "test_code": "package com.example;\\n\\nimport org.junit.jupiter.api.Test;\\nimport static org.junit.jupiter.api.Assertions.*;\\n\\npublic class ExampleTest {\\n    @Test\\n    void testMethod() {\\n        assertEquals(1, 1);\\n    }\\n}",
    "test_class_name": "ExampleTest",
    "explanation": "Test for example method"
}
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
            logger.info("=== RAW RESPONSE FROM CLAUDE START ===")
            logger.info(response_content)
            logger.info("=== RAW RESPONSE FROM CLAUDE END ===")
            
            # Try to extract JSON from the response
            # Sometimes LLM wraps JSON in markdown code blocks
            content = response_content.strip()
            
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            if content.endswith('```'):
                content = content[:-3]  # Remove ```
            
            # Parse the JSON response properly since Claude is returning valid JSON
            logger.info("Parsing JSON response from Claude")
            
            try:
                parsed_response = json.loads(content)
                logger.info("Successfully parsed JSON response from Claude")
                return parsed_response
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.info(f"Content that failed to parse: {content[:500]}...")
                # Fall back to regex extraction only if JSON parsing fails
                import re
                logger.info("Falling back to regex extraction due to JSON parsing failure")
                
                # Extract test file path
                file_path_match = re.search(r'"test_file_path":\s*"([^"]*)"', response_content)
                if not file_path_match:
                    file_path_match = re.search(r'"test_file_path"\s*[:=]\s*"([^"]*)"', response_content)
                
                # Extract test code - look for everything after test_code until the end or next field
                code_match = re.search(r'"test_code"[:"]*\s*"?(.+?)(?=",\s*"\w+"|"\s*}|\s*})', response_content, re.DOTALL)
                if not code_match:
                    # Fallback: get everything after test_code to the end
                    code_match = re.search(r'"test_code"[:"]*\s*"?(.+)', response_content, re.DOTALL)
                
                if file_path_match and code_match:
                    test_file_path = file_path_match.group(1)
                    test_code = code_match.group(1).strip()
                    
                    # Clean up the extracted code
                    if test_code.startswith('"'):
                        test_code = test_code[1:]
                    if test_code.endswith('"'):
                        test_code = test_code[:-1]
                    
                    # Unescape newlines and other escape sequences
                    test_code = test_code.replace('\\n', '\n').replace('\\"', '"')
                    
                    # Remove any trailing comma or brace
                    test_code = re.sub(r'[,}]\s*$', '', test_code).strip()
                    
                    logger.info("Successfully extracted test content using regex fallback")
                    
                    test_data = {
                        "test_file_path": test_file_path,
                        "test_code": test_code,
                        "test_class_name": self._extract_class_name(test_code),
                        "test_methods": [],
                        "imports": [],
                        "setup_code": "",
                        "explanation": "Generated Java unit test"
                    }
            else:
                logger.error("Could not extract test file path and code from response")
                return None

            
            # Generate proper relative test file path (ignore LLM's absolute path)
            file_path = function_info["file_path"]
            file_name = file_path.split('/')[-1]  # e.g., "UnusedClass.java"
            test_file_name = file_name.replace('.java', 'Test.java')  # e.g., "UnusedClassTest.java"
            
            # Convert src path to test path: src/main/java -> src/test/java
            if "src/main/java" in file_path:
                test_dir = file_path.replace("src/main/java", "src/test/java").rsplit("/", 1)[0]
            else:
                # Fallback for other structures
                test_dir = file_path.replace("src/", "src/test/").rsplit("/", 1)[0]
            
            # Ensure path is relative (remove any leading slash or absolute path)
            relative_test_path = f"{test_dir}/{test_file_name}"
            if relative_test_path.startswith('/'):
                relative_test_path = relative_test_path[1:]
            
            # Extract just the relative part if it's still absolute
            if 'src/test/' in relative_test_path:
                relative_test_path = relative_test_path[relative_test_path.find('src/test/'):]
            
            logger.info(f"Generated relative test path: {relative_test_path}")
            
            return {
                "test_file_path": relative_test_path,
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
            
            # Try one more aggressive fix for the specific Claude issue
            try:
                # Extract the test file path and code separately
                file_path_match = re.search(r'"test_file_path":\s*"([^"]*)"', content)
                
                # Find the test code after "test_code" even if malformed
                code_match = re.search(r'"test_code"[:"]*\s*([^}]+)$', content, re.DOTALL)
                
                if file_path_match and code_match:
                    test_file_path = file_path_match.group(1)
                    test_code = code_match.group(1).strip()
                    
                    # Clean up the extracted code
                    if test_code.startswith('"'):
                        test_code = test_code[1:]
                    if test_code.endswith('"'):
                        test_code = test_code[:-1]
                    
                    # Unescape newlines
                    test_code = test_code.replace('\\n', '\n')
                    
                    logger.info("Successfully extracted test content using fallback parsing")
                    
                    return {
                        "test_file_path": test_file_path,
                        "test_code": test_code,
                        "test_class_name": self._extract_class_name(test_code),
                        "test_methods": [],
                        "imports": [],
                        "setup_code": "",
                        "explanation": "Generated Java unit test"
                    }
            except Exception as fallback_error:
                logger.error(f"Fallback parsing also failed: {str(fallback_error)}")
            
            # Final fallback: try to extract code between triple backticks
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
