import logging
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISearchApiOptions(BaseSettings):
    """
    AISearch API settings loaded from environment variables and .env files.

    Attributes:
        base_url (str): Base URL for the AISearch API.
        timeout_seconds (int): Timeout for API requests in seconds.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{os.environ.get('ENV')}", ".env.loc"), env_file_encoding="utf-8", extra="allow"
    )

    base_url: str = Field(default="", validation_alias="AISEARCH_API_BASE_URL")
    timeout_seconds: int = Field(default=30, validation_alias="AISEARCH_API_TIMEOUT_SECONDS")


_logger: logging.Logger = logging.getLogger("aisearch_api_options")
_aisearch_api_options: AISearchApiOptions | None = None


def get_aisearch_api_options() -> AISearchApiOptions:
    """
    Get the singleton instance of AISearchApiOptions.

    Returns:
        AISearchApiOptions: The AISearch API settings instance.
    """
    global _aisearch_api_options
    if _aisearch_api_options is None:
        _aisearch_api_options = AISearchApiOptions()

        # Validate required configuration
        if not _aisearch_api_options.base_url:
            raise ValueError("AISEARCH_API_BASE_URL environment variable is required")
        if _aisearch_api_options.timeout_seconds < 0:
            raise ValueError("AISEARCH_API_TIMEOUT_SECONDS must be a positive integer")
        if _aisearch_api_options.timeout_seconds == 0:
            _aisearch_api_options.timeout_seconds = 30  # Default to 30 seconds if set to 0

        _logger.info("AISearch API settings loaded successfully.")

    return _aisearch_api_options


def clear_aisearch_api_options_cache() -> None:
    """
    Clear the cached options instance. Useful for testing.
    """
    global _aisearch_api_options
    _aisearch_api_options = None
