# PR Coverage Analyzer & Test Generator

A comprehensive tool that analyzes GitHub pull requests, evaluates test coverage, and automatically generates unit tests using LLM to improve code coverage.

## Features

- 📊 **Coverage Analysis**: Extract and analyze test coverage data from pull requests
- 🤖 **LLM Test Generation**: Generate intelligent unit tests using large language models
- 📝 **Automated PR Creation**: Create pull requests with improved test coverage
- 📈 **Coverage Metrics**: Compare before/after coverage statistics
- 🔗 **GitHub Integration**: Seamless integration with GitHub API

## Project Structure

```
├── src/
│   ├── analyzers/          # Coverage and code analysis modules
│   ├── generators/         # LLM-powered test generators
│   ├── github/            # GitHub API integration
│   ├── utils/             # Utility functions
│   └── main.py            # Main application entry point
├── tests/                 # Test suite
├── config/                # Configuration files
├── docs/                  # Documentation
└── requirements.txt       # Python dependencies
```

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables (see config/env.example)
4. Run the analyzer: `python src/main.py`

## Configuration

Set up your environment variables:
- `GITHUB_TOKEN`: GitHub Personal Access Token
- `OPENAI_API_KEY`: OpenAI API key for LLM test generation
- `COVERAGE_THRESHOLD`: Minimum coverage percentage target

## Usage

```python
from src.main import PRCoverageAnalyzer

analyzer = PRCoverageAnalyzer()
analyzer.analyze_pr(repo_url, pr_number)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License
