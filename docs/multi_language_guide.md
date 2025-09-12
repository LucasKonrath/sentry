# Multi-Language Support Guide

The PR Coverage Analyzer now supports multiple programming languages through standardized coverage formats and build system integration.

## Supported Languages & Build Systems

### Java Projects

#### Maven Projects
```xml
<!-- Add to your pom.xml -->
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.8</version>
    <executions>
        <execution>
            <goals>
                <goal>prepare-agent</goal>
            </goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>test</phase>
            <goals>
                <goal>report</goal>
            </goals>
            <configuration>
                <formats>
                    <format>XML</format>
                </formats>
            </configuration>
        </execution>
    </executions>
</plugin>
```

**Usage:**
```bash
# Auto-detect and build
./build.sh --repo-url https://github.com/user/java-repo --pr-number 123

# Manual Maven build
mvn clean test jacoco:report
# This generates target/site/jacoco/jacoco.xml
```

#### Gradle Projects
```kotlin
// build.gradle.kts
plugins {
    jacoco
}

jacoco {
    toolVersion = "0.8.8"
}

tasks.jacocoTestReport {
    reports {
        xml.required.set(true)
        csv.required.set(false)
        html.required.set(true)
    }
}
```

**Usage:**
```bash
# Auto-detect and build
./build.sh --repo-url https://github.com/user/gradle-repo --pr-number 123

# Manual Gradle build
./gradlew test jacocoTestReport
# This generates build/reports/jacoco/test/jacocoTestReport.xml
```

### JavaScript/TypeScript Projects

#### Package.json Configuration
```json
{
  "scripts": {
    "test": "jest",
    "test:coverage": "jest --coverage --coverageReporters=cobertura"
  },
  "jest": {
    "collectCoverage": true,
    "coverageDirectory": "coverage",
    "coverageReporters": ["cobertura", "text", "html"]
  }
}
```

**Usage:**
```bash
# Auto-detect and build  
./build.sh --repo-url https://github.com/user/js-repo --pr-number 123

# Manual build
npm test -- --coverage --coverageReporters=cobertura
# This generates coverage/cobertura-coverage.xml
```

### .NET Projects

#### Project Configuration
```xml
<!-- In your .csproj -->
<PropertyGroup>
    <CollectCoverage>true</CollectCoverage>
    <CoverletOutputFormat>cobertura</CoverletOutputFormat>
    <CoverletOutput>./coverage/</CoverletOutput>
</PropertyGroup>

<PackageReference Include="coverlet.msbuild" Version="3.2.0">
    <PrivateAssets>all</PrivateAssets>
    <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
</PackageReference>
```

**Usage:**
```bash
# Auto-detect and build
./build.sh --repo-url https://github.com/user/dotnet-repo --pr-number 123

# Manual build
dotnet test --collect:"XPlat Code Coverage" --results-directory ./TestResults
# This generates TestResults/*/coverage.cobertura.xml
```

### Python Projects

Already supported through existing configuration:

```bash
# Auto-detect and build
./build.sh --repo-url https://github.com/user/python-repo --pr-number 123

# Manual build
pytest --cov=src --cov-report=xml
# This generates coverage.xml
```

## Docker Usage

### Build Multi-Language Container
```bash
# Build the multi-language image
docker build -t pr-analyzer:multi-lang .

# Run webhook server (default)
docker run -p 5000:5000 \
  -e GITHUB_TOKEN=your_token \
  -e OPENAI_API_KEY=your_key \
  pr-analyzer:multi-lang

# Analyze Java project
docker run -v /path/to/java/project:/workspace \
  -e GITHUB_TOKEN=your_token \
  -e OPENAI_API_KEY=your_key \
  pr-analyzer:multi-lang \
  /app/build.sh --repo-url https://github.com/user/java-repo --pr-number 123

# Analyze JavaScript project  
docker run -v /path/to/js/project:/workspace \
  -e GITHUB_TOKEN=your_token \
  -e OPENAI_API_KEY=your_key \
  pr-analyzer:multi-lang \
  /app/build.sh --repo-url https://github.com/user/js-repo --pr-number 123
```

## CI/CD Integration Examples

### GitHub Actions - Java
```yaml
name: PR Coverage Analysis - Java
on:
  pull_request:
    branches: [main]

jobs:
  coverage-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up JDK 17
        uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
          
      - name: Build and Test
        run: mvn clean test jacoco:report
        
      - name: Run PR Coverage Analyzer
        run: |
          docker run -v $(pwd):/workspace \
            -e GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }} \
            -e OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }} \
            pr-analyzer:multi-lang \
            /app/build.sh --repo-url ${{ github.event.repository.html_url }} --pr-number ${{ github.event.number }}
```

### GitHub Actions - JavaScript
```yaml
name: PR Coverage Analysis - JavaScript  
on:
  pull_request:
    branches: [main]

jobs:
  coverage-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Run tests with coverage
        run: npm test -- --coverage --coverageReporters=cobertura
        
      - name: Run PR Coverage Analyzer
        run: |
          docker run -v $(pwd):/workspace \
            -e GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }} \
            -e OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }} \
            pr-analyzer:multi-lang \
            /app/build.sh --repo-url ${{ github.event.repository.html_url }} --pr-number ${{ github.event.number }}
```

## Build Script Options

The `build.sh` script automatically detects project types and builds accordingly:

```bash
# Show help
./build.sh --help

# Analyze specific repository
./build.sh --repo-url https://github.com/user/repo --pr-number 123

# Build only (no analysis)
./build.sh --build-only

# Use custom config
./build.sh --repo-url https://github.com/user/repo --pr-number 123 --config-file custom.yaml
```

## Coverage File Locations

The analyzer automatically searches for coverage files in common locations:

- **Java**: `target/site/jacoco/jacoco.xml`, `target/site/cobertura/coverage.xml`
- **JavaScript**: `coverage/cobertura-coverage.xml`, `coverage/lcov.info`
- **.NET**: `TestResults/*/coverage.cobertura.xml`, `coverage.cobertura.xml`
- **Python**: `coverage.xml`, `htmlcov/coverage.xml`

## Troubleshooting

### Java Issues
- Ensure JaCoCo plugin is properly configured
- Check that tests are actually running
- Verify XML output format is enabled

### JavaScript Issues  
- Install jest or your test framework
- Configure coverage reporters correctly
- Check Node.js version compatibility

### .NET Issues
- Install coverlet package
- Ensure test discovery is working
- Check output directory permissions

### General Issues
- Verify Docker has access to project directory
- Check environment variables are set
- Review logs in `/app/logs/` directory
