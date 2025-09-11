# Development Setup

## Installation

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp config/env.example .env
# Edit .env with your actual values
```

## Environment Variables

- `GITHUB_TOKEN`: Your GitHub Personal Access Token with repo permissions
- `OPENAI_API_KEY`: Your OpenAI API key for LLM test generation
- `COVERAGE_THRESHOLD`: Minimum coverage percentage (default: 80)
- `MIN_COVERAGE_INCREASE`: Minimum coverage improvement required (default: 5)

## Testing

Run the test suite:
```bash
pytest tests/ -v --cov=src --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

## Code Quality

Format code:
```bash
black src/ tests/
```

Lint code:
```bash
flake8 src/ tests/
```

Type checking:
```bash
mypy src/
```

## Usage Examples

### Analyze a Single PR
```bash
python src/main.py --repo-url "https://github.com/owner/repo" --pr-number 123
```

### Use Custom Configuration
```bash
python src/main.py --repo-url "https://github.com/owner/repo" --pr-number 123 --config-file custom_config.env
```

### Programmatic Usage
```python
from src.main import PRCoverageAnalyzer

analyzer = PRCoverageAnalyzer()
result = analyzer.analyze_pr("https://github.com/owner/repo", 123)
print(result)
```
