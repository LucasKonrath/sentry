# OpenAI Integration Setup

This document explains how to set up and test the OpenAI integration for the PR Coverage Analyzer project.

## Prerequisites

- An OpenAI API key (from [OpenAI platform](https://platform.openai.com))
- Python 3.8+ with the project dependencies installed

## Configuration

1. Create a `.env` file in the project root or copy from the template:

```bash
cp config/env.example .env
```

2. Add your OpenAI API key to the `.env` file:

```
OPENAI_API_KEY=sk-your-api-key-here
```

3. Configure LLM settings (optional):

```
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
MAX_TOKENS=4000
TEMPERATURE=0.2
```

## Testing the Integration

### Quick Test

Run the OpenAI smoke test script to verify connectivity:

```bash
python openai_smoke.py "Generate a unit test for a function that adds two numbers"
```

You can specify a different model with:

```bash
python openai_smoke.py --model gpt-3.5-turbo "Your prompt here"
```

### Integration Test

The integration between the PR Coverage Analyzer and OpenAI is tested with a mock in:

```bash
pytest tests/test_openai_integration.py
```

## Troubleshooting

### Common Issues

1. **API Key Invalid**: Ensure your API key is correctly formatted and has not expired.

2. **Model Compatibility**: Different OpenAI models have different parameter requirements. The smoke test attempts to handle this automatically, but you may need to specify a compatible model.

3. **Rate Limits**: If you're getting rate limit errors, you may need to wait or check your OpenAI usage limits.

4. **Network Issues**: Ensure your network can connect to the OpenAI API endpoints.

### Debugging

For more verbose output from the OpenAI API, set the following environment variable:

```bash
export OPENAI_LOG=info
```

## Using OpenAI in the Coverage Analyzer

When running the main PR Coverage Analyzer, ensure the following:

1. Your `.env` file contains the proper OpenAI configuration
2. The `LLM_PROVIDER` is set to `openai` (default)
3. Pass any custom parameters when invoking the main application:

```bash
python src/main.py --repo-url 'https://github.com/example/repo' --pr-number 123
```

The system will automatically use OpenAI to generate test cases for uncovered code areas.