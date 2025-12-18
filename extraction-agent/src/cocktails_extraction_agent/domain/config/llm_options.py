import logging
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMOptions(BaseSettings):
    """LLM configuration options loaded from environment variables and .env files.  The options include LLM service host and Langfuse integration settings.

    Attributes:
        llm_host (str): The host URL for the LLM service.
        langfuse_host (str): The base URL for Langfuse integration.
        langfuse_public_key (str): The public key for Langfuse authentication.
        langfuse_secret_key (str): The secret key for Langfuse authentication.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{os.environ.get('ENV')}"), env_file_encoding="utf-8", extra="allow"
    )

    llm_host: str | None = Field(default=None, validation_alias="LLM_HOST")
    langfuse_host: str = Field(default="", validation_alias="LANGFUSE_BASE_URL")
    langfuse_public_key: str = Field(default="", validation_alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", validation_alias="LANGFUSE_SECRET_KEY")


_logger: logging.Logger = logging.getLogger("llm_config")

_llm_options: LLMOptions | None = None


def get_llm_options() -> LLMOptions:
    """Get the singleton instance of LLMOptions.

    Returns:
        LLMOptions: The LLM options instance.
    """
    global _llm_options
    if _llm_options is None:
        _llm_options = LLMOptions()

        # Validate required configuration
        if _llm_options.langfuse_host:
            if not _llm_options.langfuse_public_key:
                raise ValueError("LANGFUSE_PUBLIC_KEY environment variable is required when LANGFUSE_BASE_URL is set")
            if not _llm_options.langfuse_secret_key:
                raise ValueError("LANGFUSE_SECRET_KEY environment variable is required when LANGFUSE_BASE_URL is set")

        _logger.info("LLM options loaded successfully.")

        if _llm_options.langfuse_host:
            if not os.environ.get("LANGFUSE_BASE_URL"):
                os.environ["LANGFUSE_BASE_URL"] = _llm_options.langfuse_host
            if not os.environ.get("LANGFUSE_HOST"):
                os.environ["LANGFUSE_HOST"] = _llm_options.langfuse_host
            if not os.environ.get("LANGFUSE_PUBLIC_KEY"):
                os.environ["LANGFUSE_PUBLIC_KEY"] = _llm_options.langfuse_public_key
            if not os.environ.get("LANGFUSE_SECRET_KEY"):
                os.environ["LANGFUSE_SECRET_KEY"] = _llm_options.langfuse_secret_key

            _logger.info("Langfuse options loaded into environment.")

    return _llm_options


def clear_llm_options_cache() -> None:
    """Clear the cached options instance. Useful for testing."""
    global _llm_options
    _llm_options = None
