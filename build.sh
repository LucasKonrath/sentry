#!/bin/bash
# Multi-language project analyzer build script
# Supports Python, Java, C#, and JavaScript projects

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Multi-Language PR Coverage Analyzer${NC}"
echo "========================================"

# Function to detect project type
detect_project_type() {
    local project_types=()
    
    if [[ -f "pom.xml" || -f "build.gradle" || -f "build.gradle.kts" ]]; then
        project_types+=("java")
    fi
    
    if [[ -f "package.json" ]]; then
        project_types+=("javascript")
    fi
    
    if [[ -f "requirements.txt" || -f "setup.py" || -f "pyproject.toml" ]]; then
        project_types+=("python")
    fi
    
    if [[ -f "*.csproj" || -f "*.sln" || -f "Directory.Build.props" ]]; then
        project_types+=("dotnet")
    fi
    
    echo "${project_types[@]}"
}

# Function to build Java project
build_java() {
    echo -e "${YELLOW}📦 Building Java project...${NC}"
    
    if [[ -f "pom.xml" ]]; then
        echo "Maven project detected"
        if ! command -v mvn &> /dev/null; then
            echo -e "${RED}❌ Maven not found. Installing...${NC}"
            # Install Maven if not present
            if command -v apt-get &> /dev/null; then
                sudo apt-get update && sudo apt-get install -y maven
            elif command -v brew &> /dev/null; then
                brew install maven
            else
                echo -e "${RED}❌ Cannot install Maven automatically${NC}"
                exit 1
            fi
        fi
        
        # Build with coverage
        mvn clean compile test jacoco:report
        
        # Check if JaCoCo coverage report was generated
        if [[ -f "target/site/jacoco/jacoco.xml" ]]; then
            echo -e "${GREEN}✅ Generated JaCoCo coverage report: target/site/jacoco/jacoco.xml${NC}"
        else
            echo -e "${YELLOW}⚠️  Warning: JaCoCo coverage report not found${NC}"
        fi
        
    elif [[ -f "build.gradle" || -f "build.gradle.kts" ]]; then
        echo "Gradle project detected"
        if ! command -v gradle &> /dev/null; then
            if [[ -f "gradlew" ]]; then
                echo "Using Gradle wrapper"
                ./gradlew clean build jacocoTestReport
            else
                echo -e "${RED}❌ Gradle not found and no wrapper available${NC}"
                exit 1
            fi
        else
            gradle clean build jacocoTestReport
        fi
    fi
}

# Function to build JavaScript project  
build_javascript() {
    echo -e "${YELLOW}📦 Building JavaScript project...${NC}"
    
    if [[ -f "package.json" ]]; then
        if command -v npm &> /dev/null; then
            npm install
            npm test -- --coverage --coverageReporters=cobertura
        elif command -v yarn &> /dev/null; then
            yarn install
            yarn test --coverage --coverageReporters=cobertura
        else
            echo -e "${RED}❌ Neither npm nor yarn found${NC}"
            exit 1
        fi
    fi
}

# Function to build .NET project
build_dotnet() {
    echo -e "${YELLOW}📦 Building .NET project...${NC}"
    
    if ! command -v dotnet &> /dev/null; then
        echo -e "${RED}❌ .NET CLI not found${NC}"
        exit 1
    fi
    
    dotnet restore
    dotnet build
    dotnet test --collect:"XPlat Code Coverage" --results-directory ./TestResults \
        -- DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=cobertura
}

# Function to build Python project
build_python() {
    echo -e "${YELLOW}📦 Building Python project...${NC}"
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d ".venv" ]]; then
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Install dependencies
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    fi
    
    # Set PYTHONPATH for testing
    export PYTHONPATH="${PWD}:${PYTHONPATH:-}"
    
    # Run tests with coverage
    if command -v pytest &> /dev/null; then
        pytest --cov=src --cov-report=xml --cov-report=term
    else
        python -m coverage run -m pytest
        python -m coverage xml
    fi
}

# Function to run the analyzer
run_analyzer() {
    echo -e "${YELLOW}🔍 Running PR Coverage Analyzer...${NC}"
    
    # Ensure Python environment for the analyzer
    if [[ ! -d ".venv" ]]; then
        python3 -m venv .venv
    fi
    
    source .venv/bin/activate
    
    # Install analyzer dependencies if needed
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    fi
    
    # Run the analyzer with provided arguments
    python src/main.py "$@"
}

# Main execution
main() {
    local repo_url=""
    local pr_number=""
    local config_file=""
    local build_only=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --repo-url)
                repo_url="$2"
                shift 2
                ;;
            --pr-number)
                pr_number="$2"
                shift 2
                ;;
            --config-file)
                config_file="$2"
                shift 2
                ;;
            --build-only)
                build_only=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --repo-url URL        GitHub repository URL"
                echo "  --pr-number NUM       Pull request number"
                echo "  --config-file FILE    Configuration file path"
                echo "  --build-only          Only build projects, don't run analyzer"
                echo "  -h, --help           Show this help"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                exit 1
                ;;
        esac
    done
    
    # Detect project types
    project_types=($(detect_project_type))
    
    if [[ ${#project_types[@]} -eq 0 ]]; then
        echo -e "${YELLOW}⚠️  No supported project type detected${NC}"
        echo "Supported: Maven (pom.xml), Gradle (build.gradle), Node.js (package.json), .NET (*.csproj), Python (requirements.txt)"
    else
        echo -e "${GREEN}✅ Detected project types: ${project_types[*]}${NC}"
        
        # Build each detected project type
        for project_type in "${project_types[@]}"; do
            case $project_type in
                java)
                    build_java
                    ;;
                javascript)
                    build_javascript
                    ;;
                dotnet)
                    build_dotnet
                    ;;
                python)
                    build_python
                    ;;
            esac
        done
    fi
    
    # Run analyzer unless build-only mode
    if [[ "$build_only" = false ]]; then
        if [[ -n "$repo_url" && -n "$pr_number" ]]; then
            local analyzer_args=(--repo-url "$repo_url" --pr-number "$pr_number")
            if [[ -n "$config_file" ]]; then
                analyzer_args+=(--config-file "$config_file")
            fi
            run_analyzer "${analyzer_args[@]}"
        else
            echo -e "${YELLOW}⚠️  Skipping analyzer - missing repo-url or pr-number${NC}"
            echo "Use --repo-url and --pr-number to run the analyzer"
        fi
    fi
    
    echo -e "${GREEN}✅ Build complete!${NC}"
}

# Run main function with all arguments
main "$@"
