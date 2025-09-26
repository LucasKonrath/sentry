"""Simple smoke test to verify OpenAI API connectivity using existing configuration.

Usage:
  python openai_smoke.py "Brief prompt here"

Requires environment variables:
  OPENAI_API_KEY (and optionally LLM_MODEL, MAX_TOKENS, TEMPERATURE)
"""
import os
import sys
import json
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

try:
    import openai
except ImportError:
    print("openai package not installed. Add 'openai' to requirements and install.")
    sys.exit(1)

# Allow forcing model for testing
FORCE_MODEL = None
if "--model" in sys.argv:
    model_idx = sys.argv.index("--model")
    if model_idx < len(sys.argv) - 1:
        FORCE_MODEL = sys.argv[model_idx + 1]
        # Remove these args so they don't interfere with the prompt
        sys.argv.pop(model_idx)
        sys.argv.pop(model_idx)

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("❌ OPENAI_API_KEY not set. Export it and retry.")
    sys.exit(1)

client = openai.OpenAI(api_key=API_KEY)
model = FORCE_MODEL or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
max_tokens = int(os.getenv("MAX_TOKENS", "256"))
temperature = float(os.getenv("TEMPERATURE", "0.2"))

user_prompt = " ".join(sys.argv[1:]) or "Say hello in one short sentence."

print(f"➡️  Sending prompt to OpenAI model={model} ...")
try:
    # Different models require different parameters, try safe defaults first
    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": user_prompt},
        ]
    }
    
    # Only add params known to work with this model
    if model.startswith("o3-") or model.startswith("claude-"):
        # Most o3 models use max_completion_tokens
        kwargs["max_completion_tokens"] = max_tokens
    else:
        # Standard parameter for most models
        kwargs["max_tokens"] = max_tokens
        
    # Add temperature only for models that support it
    if not model.startswith("o3-"):
        kwargs["temperature"] = temperature
        
    print(f"Parameters: {json.dumps(kwargs, default=str)}")
    resp = client.chat.completions.create(**kwargs)
    print("✅ Success\n--- Response ---\n" + resp.choices[0].message.content.strip())
except Exception as e:
    print(f"❌ OpenAI call failed: {e}")
    sys.exit(2)
