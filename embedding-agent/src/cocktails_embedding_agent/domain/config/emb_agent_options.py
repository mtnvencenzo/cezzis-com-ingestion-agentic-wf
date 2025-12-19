import logging
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingAgentOptions(BaseSettings):
    """Application settings loaded from environment variables and .env files.

    Attributes:
        enabled (bool): Flag to enable or disable the embedding agent.
        consumer_topic_name (str): Kafka embedding topic name.
        num_consumers (int): Number of Kafka consumer processes to start.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{os.environ.get('ENV')}"), env_file_encoding="utf-8", extra="allow"
    )

    enabled: bool = Field(default=True, validation_alias="EMBEDDING_AGENT_ENABLED")
    consumer_topic_name: str = Field(default="", validation_alias="EMBEDDING_AGENT_KAFKA_TOPIC_NAME")
    num_consumers: int = Field(default=1, validation_alias="EMBEDDING_AGENT_KAFKA_NUM_CONSUMERS")


_logger: logging.Logger = logging.getLogger("emb_agent_options")

_emb_agent_options: EmbeddingAgentOptions | None = None


def get_emb_agent_options() -> EmbeddingAgentOptions:
    """Get the singleton instance of EmbeddingAgentOptions.

    Returns:
        EmbeddingAgentOptions: The application settings instance.
    """
    global _emb_agent_options
    if _emb_agent_options is None:
        _emb_agent_options = EmbeddingAgentOptions()

        # Validate required configuration
        if not _emb_agent_options.consumer_topic_name:
            raise ValueError("EMBEDDING_AGENT_KAFKA_TOPIC_NAME environment variable is required")
        if not _emb_agent_options.num_consumers or _emb_agent_options.num_consumers < 1:
            raise ValueError("EMBEDDING_AGENT_KAFKA_NUM_CONSUMERS environment variable must be a positive integer")

        _logger.info("Embedding agent app settings loaded successfully.")

    return _emb_agent_options


def clear_emb_agent_options_cache() -> None:
    """Clear the cached options instance. Useful for testing."""
    global _emb_agent_options
    _emb_agent_options = None
