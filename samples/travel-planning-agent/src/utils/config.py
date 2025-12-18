"""
Configuration management for Travel Planning Agent
Uses Pydantic for validation and type safety
"""

import os
import uuid
from typing import Optional, Any, Dict
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class LLMConfig(BaseSettings):
    """LLM Provider Configuration"""
    provider: str = Field(default="openai", alias="LLM_PROVIDER")
    base_url: Optional[str] = Field(default=None, alias="LLM_BASE_URL")
    openai_api_key: Optional[str] = Field(default="dummy-key", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")
    anthropic_api_key: Optional[str] = Field(default="dummy-key", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-opus-20240229", alias="ANTHROPIC_MODEL")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=4096)

    class Config:
        env_file = ".env"
        extra = "allow"

    @property
    def model(self) -> str:
        """Get the model name based on provider"""
        if self.provider == "anthropic":
            return self.anthropic_model
        return self.openai_model


class SearchConfig(BaseSettings):
    """Search API Configuration"""
    provider: str = Field(default="tavily", alias="SEARCH_PROVIDER")
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    serpapi_api_key: Optional[str] = Field(default=None, alias="SERPAPI_API_KEY")

    class Config:
        env_prefix = ""
        extra = "ignore"


class AgentConfig(BaseSettings):
    """Agent Behavior Configuration"""
    max_iterations: int = Field(default=20, alias="MAX_ITERATIONS")
    request_timeout: int = Field(default=30, alias="REQUEST_TIMEOUT")

    class Config:
        env_prefix = ""
        extra = "ignore"


class AppConfig(BaseSettings):
    """Application Settings"""
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    output_dir: str = Field(default="./outputs", alias="OUTPUT_DIR")
    mock_external_apis: bool = Field(default=False, alias="MOCK_EXTERNAL_APIS")
    debug_mode: bool = Field(default=False, alias="DEBUG_MODE")

    class Config:
        env_prefix = ""
        extra = "ignore"


class Config:
    """Main configuration container"""

    def __init__(self):
        self.llm = LLMConfig()
        self.search = SearchConfig()
        self.agent = AgentConfig()
        self.app = AppConfig()

        # Observability IDs (set per run)
        self.thread_id: Optional[str] = None
        self.run_id: Optional[str] = None

    def generate_ids(self) -> tuple:
        """Generate unique thread and run IDs (UUIDs)"""
        self.thread_id = str(uuid.uuid4())
        self.run_id = str(uuid.uuid4())
        return self.thread_id, self.run_id

    def get_llm_client(self, label: Optional[str] = None):
        """
        Get LLM client with observability headers

        Args:
            label: Label for tracing (e.g., "research_agent", "orchestrator")

        Returns:
            OpenAI or Anthropic client
        """
        if self.llm.provider == "openai":
            from openai import OpenAI

            # Build headers for observability
            default_headers = {}
            if self.thread_id:
                default_headers["x-thread-id"] = self.thread_id
            if self.run_id:
                default_headers["x-run-id"] = self.run_id
            if label:
                default_headers["x-label"] = label

            return OpenAI(
                api_key=self.llm.openai_api_key or "dummy-key",
                base_url=self.llm.base_url,
                default_headers=default_headers if default_headers else None
            )
        elif self.llm.provider == "anthropic":
            from anthropic import Anthropic

            return Anthropic(
                api_key=self.llm.anthropic_api_key
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm.provider}")

    def get_llm_params(self) -> Dict[str, Any]:
        """Get LLM parameters for API calls"""
        if self.llm.provider == "openai":
            return {
                "model": self.llm.openai_model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens
            }
        elif self.llm.provider == "anthropic":
            return {
                "model": self.llm.anthropic_model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens
            }
        return {}

    def validate(self) -> bool:
        """Validate configuration"""
        valid = True

        # Check LLM configuration
        if self.llm.provider == "openai":
            if not self.llm.base_url and not self.llm.openai_api_key:
                print("Warning: No OpenAI API key or base URL configured")
                print("  Set OPENAI_API_KEY or OPENAI_BASE_URL in .env")
                valid = False
        elif self.llm.provider == "anthropic":
            if not self.llm.anthropic_api_key:
                print("Warning: No Anthropic API key configured")
                valid = False

        # Check search configuration
        if not self.search.tavily_api_key and not self.search.serpapi_api_key:
            if self.app.mock_external_apis:
                print("Note: No search API keys configured - using mock search")
            else:
                print("Warning: No search API keys configured and MOCK_EXTERNAL_APIS=false")
                print("  Set TAVILY_API_KEY or SERPAPI_API_KEY in .env")
                valid = False

        return valid


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config
