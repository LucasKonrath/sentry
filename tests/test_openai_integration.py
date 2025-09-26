import types
import os
import sys
import pytest
from src.generators.test_generator import TestGenerator
from src.utils.config import Config

class DummyChoice:
    def __init__(self, content):
        self.message = types.SimpleNamespace(content=content)

class DummyResponse:
    def __init__(self, text):
        self.choices = [DummyChoice(text)]

class DummyChatCompletions:
    def create(self, **kwargs):
        # Basic assertion of expected keys
        assert 'model' in kwargs
        assert 'messages' in kwargs
        return DummyResponse("TEST_OK")

class DummyOpenAIClient:
    def __init__(self):
        self.chat = types.SimpleNamespace(completions=DummyChatCompletions())

def test_openai_call_mock(monkeypatch):
    # Patch openai import in TestGenerator init path
    dummy_module = types.SimpleNamespace(OpenAI=lambda api_key=None: DummyOpenAIClient())
    monkeypatch.setitem(sys.modules, 'openai', dummy_module)

    # Provide fake API key so initialization proceeds
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test')
    cfg = Config()
    cfg.llm_provider = 'openai'
    cfg.openai_api_key = 'sk-test'

    gen = TestGenerator(cfg)
    assert gen._is_client_configured()
    out = gen._call_llm('system', 'user prompt')
    assert out == 'TEST_OK'
