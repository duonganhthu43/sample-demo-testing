"""
Configuration Management
"""

import os
from typing import Optional, Any
from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class LLMConfig(BaseSettings):
    """LLM Configuration"""
    provider: str = Field(default="openai", description="LLM provider: openai or anthropic")

    # Local LLM Gateway (e.g., LiteLLM, Ollama, etc.)
    base_url: Optional[str] = Field(default=None, alias="LLM_BASE_URL")
    use_local_gateway: bool = Field(default=False, alias="USE_LOCAL_GATEWAY")

    # OpenAI
    openai_api_key: Optional[str] = Field(default="dummy-key", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")
    openai_temperature: Optional[float] = Field(default=None, alias="OPENAI_TEMPERATURE")
    openai_max_tokens: Optional[int] = Field(default=None, alias="OPENAI_MAX_TOKENS")

    # Anthropic
    anthropic_api_key: Optional[str] = Field(default="dummy-key", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-opus-20240229", alias="ANTHROPIC_MODEL")
    anthropic_temperature: float = Field(default=0.7, alias="ANTHROPIC_TEMPERATURE")
    anthropic_max_tokens: int = Field(default=4000, alias="ANTHROPIC_MAX_TOKENS")

    class Config:
        env_file = ".env"
        extra = "allow"


class SearchConfig(BaseSettings):
    """Search API Configuration"""
    provider: str = Field(default="serpapi", alias="SEARCH_PROVIDER")
    serpapi_api_key: Optional[str] = Field(default=None, alias="SERPAPI_API_KEY")
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")

    class Config:
        env_file = ".env"
        extra = "allow"


class ObservabilityConfig(BaseSettings):
    """Observability Platform Configuration"""
    enabled: bool = Field(default=True, alias="OBSERVABILITY_ENABLED")
    api_key: Optional[str] = Field(default=None, alias="OBSERVABILITY_API_KEY")
    endpoint: Optional[str] = Field(default=None, alias="OBSERVABILITY_ENDPOINT")
    project_name: str = Field(default="market-research-agent", alias="OBSERVABILITY_PROJECT_NAME")
    environment: str = Field(default="development", alias="OBSERVABILITY_ENVIRONMENT")

    class Config:
        env_file = ".env"
        extra = "allow"


class AgentConfig(BaseSettings):
    """Agent Configuration"""
    max_iterations: int = Field(default=10, alias="MAX_AGENT_ITERATIONS")
    timeout: int = Field(default=300, alias="AGENT_TIMEOUT")
    enable_caching: bool = Field(default=True, alias="ENABLE_CACHING")
    enable_parallel_execution: bool = Field(default=True, alias="ENABLE_PARALLEL_EXECUTION")

    class Config:
        env_file = ".env"
        extra = "allow"


class AppConfig(BaseSettings):
    """Application Configuration"""
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    output_dir: str = Field(default="./outputs", alias="OUTPUT_DIR")
    enable_rich_output: bool = Field(default=True, alias="ENABLE_RICH_OUTPUT")
    save_intermediate_results: bool = Field(default=True, alias="SAVE_INTERMEDIATE_RESULTS")
    debug_mode: bool = Field(default=False, alias="DEBUG_MODE")
    mock_external_apis: bool = Field(default=False, alias="MOCK_EXTERNAL_APIS")
    save_prompts_responses: bool = Field(default=True, alias="SAVE_PROMPTS_RESPONSES")

    # Rate limiting
    max_api_calls_per_minute: int = Field(default=60, alias="MAX_API_CALLS_PER_MINUTE")
    max_cost_per_analysis: float = Field(default=5.0, alias="MAX_COST_PER_ANALYSIS")
    enable_cost_tracking: bool = Field(default=True, alias="ENABLE_COST_TRACKING")

    class Config:
        env_file = ".env"
        extra = "allow"


class Config:
    """Main configuration object"""

    def __init__(self):
        self.llm = LLMConfig()
        self.search = SearchConfig()
        self.observability = ObservabilityConfig()
        self.agent = AgentConfig()
        self.app = AppConfig()

        # Thread ID for grouping traces (set by orchestrator)
        self.thread_id: Optional[str] = None

        # Run ID for grouping traces in same run (set by orchestrator)
        self.run_id: Optional[str] = None

        # Create output directory
        Path(self.app.output_dir).mkdir(parents=True, exist_ok=True)

    def validate(self) -> bool:
        """Validate configuration"""
        errors = []

        # Check LLM configuration
        if self.llm.use_local_gateway or self.llm.base_url:
            # Using local LLM gateway - no API key validation needed
            if not self.llm.base_url:
                errors.append("LLM_BASE_URL is required when USE_LOCAL_GATEWAY=true")
            else:
                print(f"✓ Using local LLM gateway: {self.llm.base_url}")
        else:
            # Using cloud providers - check API keys
            if self.llm.provider == "openai" and (not self.llm.openai_api_key or self.llm.openai_api_key == "dummy-key"):
                errors.append("OPENAI_API_KEY is required when using OpenAI (or set USE_LOCAL_GATEWAY=true)")

            if self.llm.provider == "anthropic" and (not self.llm.anthropic_api_key or self.llm.anthropic_api_key == "dummy-key"):
                errors.append("ANTHROPIC_API_KEY is required when using Anthropic (or set USE_LOCAL_GATEWAY=true)")

        # Check search API keys (only if not mocking)
        if not self.app.mock_external_apis:
            if self.search.provider == "serpapi" and not self.search.serpapi_api_key:
                print("⚠️  SERPAPI_API_KEY not set - will use mock search results")
                # Don't error, just use mock mode

            if self.search.provider == "tavily" and not self.search.tavily_api_key:
                print("⚠️  TAVILY_API_KEY not set - will use mock search results")
                # Don't error, just use mock mode

        if errors:
            print("Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True

    def get_llm_client(self, label: Optional[str] = None):
        """Get configured LLM client with thread ID, run ID, and label headers"""
        # Prepare headers with thread ID, run ID, and label if available
        headers = {}
        if self.thread_id:
            headers["x-thread-id"] = self.thread_id
        if self.run_id:
            headers["x-run-id"] = self.run_id
        if label:
            headers["x-label"] = label

        if self.llm.provider == "openai":
            from openai import OpenAI

            # Use local gateway if configured
            if self.llm.base_url:
                return OpenAI(
                    api_key=self.llm.openai_api_key,
                    base_url=self.llm.base_url,
                    default_headers=headers if headers else None
                )
            else:
                return OpenAI(
                    api_key=self.llm.openai_api_key,
                    default_headers=headers if headers else None
                )

        elif self.llm.provider == "anthropic":
            from anthropic import Anthropic

            # Use local gateway if configured
            if self.llm.base_url:
                return Anthropic(
                    api_key=self.llm.anthropic_api_key,
                    base_url=self.llm.base_url,
                    default_headers=headers if headers else None
                )
            else:
                return Anthropic(
                    api_key=self.llm.anthropic_api_key,
                    default_headers=headers if headers else None
                )

        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm.provider}")

    def get_llm_params(self) -> dict:
        """Get LLM parameters for API calls"""
        if self.llm.provider == "openai":
            return {
                "model": self.llm.openai_model
            }

        elif self.llm.provider == "anthropic":
            return {
                "model": self.llm.anthropic_model,
                "temperature": self.llm.anthropic_temperature,
                "max_tokens": self.llm.anthropic_max_tokens
            }

        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm.provider}")


# Global config instance
_global_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global config instance"""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config
