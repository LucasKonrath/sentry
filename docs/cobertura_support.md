# Cobertura Coverage Support

The PR Coverage Analyzer now supports **Cobertura XML coverage format**, which is widely used across multiple programming languages and build systems.

## Supported Coverage Formats

### ✅ **Currently Supported:**
- **Cobertura XML** - Universal format used by many tools
- **pytest-cov JSON** - Python testing coverage
- **Istanbul/NYC JSON** - JavaScript/TypeScript coverage
- **LCOV** - Linux Test Project format (partial support)

### 🔄 **Automatically Detected:**
The analyzer automatically searches for and detects coverage reports in these locations:

```
coverage.xml                          # Standard Cobertura
cobertura-coverage.xml               # Alternative naming
target/site/cobertura/coverage.xml   # Maven projects
build/reports/cobertura/coverage.xml # Gradle projects
coverage/cobertura-coverage.xml      # Custom locations
TestResults/coverage.cobertura.xml   # .NET projects
```

## Language & Tool Support

### **Java**
```xml
<!-- Maven (pom.xml) -->
<plugin>
  <groupId>org.codehaus.mojo</groupId>
  <artifactId>cobertura-maven-plugin</artifactId>
  <version>2.7</version>
  <configuration>
    <formats>
      <format>xml</format>
    </formats>
  </configuration>
</plugin>
```

```groovy
// Gradle (build.gradle)
plugins {
    id 'net.saliman.cobertura' version '4.0.0'
}

cobertura {
    coverageFormats = ['xml']
}
```

### **Python**
```bash
# Using pytest-cov with Cobertura output
pytest --cov=src --cov-report=xml:coverage.xml

# Using coverage.py directly
coverage run -m pytest
coverage xml -o coverage.xml
```

### **C#/.NET**
```bash
# Using coverlet
dotnet test --collect:"XPlat Code Coverage" --results-directory ./TestResults/
# Generates: TestResults/*/coverage.cobertura.xml

# Using ReportGenerator to convert
reportgenerator "-reports:TestResults/*/coverage.cobertura.xml" "-targetdir:coverage" "-reporttypes:Cobertura"
```

### **JavaScript/TypeScript**
```json
{
  "scripts": {
    "test:coverage": "jest --coverage --coverageReporters=cobertura"
  },
  "jest": {
    "coverageReporters": ["cobertura", "text", "html"]
  }
}
```

### **Go**
```bash
# Generate coverage and convert to Cobertura
go test -coverprofile=coverage.out ./...
gocover-cobertura < coverage.out > coverage.xml
```

## Configuration Examples

### **Repository-Specific Settings**
Update `config/target_repos.yml` to specify coverage format preferences:

```yaml
repositories:
  - owner: myorg
    name: java-backend
    settings:
      coverage_threshold: 80
      languages: [java]
      coverage_format: cobertura
      coverage_file: target/site/cobertura/coverage.xml
      
  - owner: myorg
    name: dotnet-api
    settings:
      coverage_threshold: 85
      languages: [csharp]
      coverage_format: cobertura
      coverage_file: TestResults/coverage.cobertura.xml
      
  - owner: myorg
    name: python-service
    settings:
      coverage_threshold: 90
      languages: [python]
      coverage_format: pytest-json  # Can still use JSON for Python
      coverage_file: coverage.json
```

### **Multi-Format Support**
The analyzer can handle mixed repositories:

```yaml
# Global settings for fallback
global_settings:
  coverage_formats:
    - cobertura    # Try Cobertura XML first
    - pytest-json  # Then pytest JSON
    - istanbul     # Then Istanbul JSON
    - lcov         # Finally LCOV
  
  search_paths:
    - "coverage.xml"
    - "target/site/cobertura/coverage.xml"  
    - "build/reports/jacoco/test/jacocoTestReport.xml"
    - "coverage.json"
    - "coverage/lcov.info"
```

## GitHub Actions Integration

### **Java Project Example**
```yaml
name: PR Coverage Analysis (Java)

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  analyze-coverage:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up JDK
      uses: actions/setup-java@v4
      with:
        java-version: '11'
        distribution: 'temurin'
    
    - name: Run tests with coverage
      run: |
        # Maven
        mvn clean test cobertura:cobertura
        # OR Gradle
        # ./gradlew test cobertura
    
    - name: Run PR Coverage Analysis
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        # The analyzer will auto-detect target/site/cobertura/coverage.xml
        python -m src.main --repo-url "${{ github.repository }}" --pr-number "${{ github.event.number }}"
```

### **.NET Project Example**
```yaml
- name: Test with coverage
  run: |
    dotnet test --collect:"XPlat Code Coverage" --results-directory ./TestResults/
    
- name: Run PR Coverage Analysis  
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    # Auto-detects TestResults/*/coverage.cobertura.xml
    python -m src.main --repo-url "${{ github.repository }}" --pr-number "${{ github.event.number }}"
```

## Parsed Coverage Data

### **Cobertura XML Structure**
The parser extracts comprehensive coverage information:

```python
{
    'overall_coverage': 78.5,           # Overall line coverage percentage
    'file_coverage': {
        'src/Calculator.java': {
            'summary': {
                'percent_covered': 85.7,
                'line_rate': 0.857,
                'branch_rate': 0.75
            },
            'missing_lines': [26, 36],      # Lines with 0 hits
            'covered_lines': [8, 12, 16],   # Lines with hits > 0  
            'partial_lines': [25, 33],      # Branch lines with partial coverage
            'line_details': {
                25: {
                    'hits': 4,
                    'branch': True,
                    'condition_coverage': '50% (1/2)'
                }
            }
        }
    },
    'source_format': 'cobertura',
    'metadata': {
        'timestamp': '1640995200000',
        'version': '1.0',
        'source_paths': ['src/main/java']
    }
}
```

### **Enhanced Test Generation**
The Cobertura support enables more intelligent test generation:

- **Method-Level Analysis** - Identifies specific methods needing coverage
- **Branch Coverage** - Generates tests for uncovered conditional branches  
- **Class-Level Metrics** - Prioritizes classes with low coverage
- **Package Organization** - Groups related coverage improvements

## Troubleshooting

### **Common Issues**

1. **Coverage file not found**
   ```bash
   # Ensure your build generates Cobertura XML
   mvn cobertura:cobertura -Dcobertura.report.format=xml
   ```

2. **Invalid XML format**
   ```bash
   # Validate your coverage.xml
   xmllint --noout coverage.xml
   ```

3. **Wrong file paths**
   ```yaml
   # Specify exact coverage file location
   coverage_file: "custom/path/to/coverage.xml"
   ```

### **Debug Coverage Detection**
Enable debug logging to see which coverage files are detected:

```bash
LOG_LEVEL=DEBUG python -m src.main --repo-url "..." --pr-number 123
```

## Benefits of Cobertura Support

### ✅ **Universal Compatibility**
- Works with Java, C#, Python, JavaScript, and more
- Consistent format across different tools and languages
- Industry-standard XML format

### 📊 **Rich Coverage Data**  
- Line-level coverage with hit counts
- Branch/condition coverage analysis
- Method and class-level granularity
- Source path information

### 🎯 **Precise Test Generation**
- Identifies exact uncovered lines
- Understands branch coverage gaps
- Generates targeted test cases
- Prioritizes by coverage impact

Your PR Coverage Analyzer now supports the most widely-used coverage format, making it compatible with virtually any development stack! 🚀
