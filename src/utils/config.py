"""
Configuration management for the PR Coverage Analyzer.
"""

import os
from typing import Dict, Any, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration using Pydantic for validation."""
    
    # GitHub Settings
    github_token: str = Field("", env="GITHUB_TOKEN")
    default_branch: str = Field("main", env="DEFAULT_BRANCH")
    pr_branch_prefix: str = Field("auto-tests/", env="PR_BRANCH_PREFIX")
    pr_title_prefix: str = Field("[Auto] Add unit tests to improve coverage", env="PR_TITLE_PREFIX")
    
    # LLM Provider Settings
    llm_provider: str = Field("openai", env="LLM_PROVIDER")  # openai or claude
    
    # OpenAI Settings
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    
    # Claude Settings
    anthropic_api_key: str = Field("", env="ANTHROPIC_API_KEY")
    
    # Common LLM Settings
    llm_model: str = Field("gpt-4", env="LLM_MODEL")
    max_tokens: int = Field(4000, env="MAX_TOKENS")
    temperature: float = Field(0.2, env="TEMPERATURE")
    
    # Coverage Settings
    coverage_threshold: int = Field(80, env="COVERAGE_THRESHOLD")
    min_coverage_increase: int = Field(5, env="MIN_COVERAGE_INCREASE")
    
    # Analysis Settings
    supported_languages: List[str] = Field(
        ["python", "javascript", "typescript", "java"], 
        env="SUPPORTED_LANGUAGES"
    )
    exclude_patterns: List[str] = Field(
        ["*.pyc", "__pycache__", "node_modules", "*.git"], 
        env="EXCLUDE_PATTERNS"
    )
    
    # Logging Settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
        env="LOG_FORMAT"
    )
    
    # Testing Settings
    local_mode: bool = Field(True, env="LOCAL_MODE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return self.dict()
        
    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
        """Load configuration from file."""
        if os.path.exists(config_path):
            return cls(_env_file=config_path)
        return cls()
