import os
from src.analyzers.code_analyzer import CodeAnalyzer
from src.utils.config import Config


def test_fuzzy_resolution_missing_java_file():
    config = Config()
    analyzer = CodeAnalyzer(config)
    # Path without package (does not exist physically)
    truncated = os.path.join('src', 'main', 'java', 'SimpleCalculator.java')
    result = analyzer._analyze_file_structure(truncated)
    # Should resolve to actual java file under test-java-project if present
    actual = 'test-java-project/src/main/java/com/example/calculator/SimpleCalculator.java'
    if os.path.exists(actual):
        assert result is not None, "Expected fuzzy resolver to find SimpleCalculator.java"
        assert result.get('language') == 'java'
    else:
        # If layout changes, ensure no crash
        assert result is None or isinstance(result, dict)
