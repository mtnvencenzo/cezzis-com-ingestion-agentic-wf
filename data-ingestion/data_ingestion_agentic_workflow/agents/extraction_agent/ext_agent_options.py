import logging
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExtractionAgentOptions(BaseSettings):
    """Application settings loaded from environment variables and .env files.

    Attributes:
        enabled (bool): Flag to enable or disable the extraction agent.
        bootstrap_servers (str): Kafka bootstrap servers.
        consumer_group (str): Kafka consumer group ID.
        extraction_topic_name (str): Kafka extraction topic name.
        embedding_topic_name (str): Kafka embedding topic name.
        num_consumers (int): Number of Kafka consumer processes to start.
        ollama_host (str): The host and port to reach ollama from.
        langfuse_host (str): The host URL for Langfuse.
        langfuse_public_key (str): The public key for Langfuse.
        langfuse_secret_key (str): The secret key for Langfuse.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{os.environ.get('ENV')}"), env_file_encoding="utf-8", extra="allow"
    )

    enabled: bool = Field(default=True, validation_alias="AGENTS_ENABLE_EXTRACTION_AGENT")
    bootstrap_servers: str = Field(default="", validation_alias="KAFKA_BOOTSTRAP_SERVERS")
    consumer_group: str = Field(default="", validation_alias="KAFKA_CONSUMER_GROUP")
    extraction_topic_name: str = Field(default="", validation_alias="KAFKA_EXTRACTION_TOPIC_NAME")
    embedding_topic_name: str = Field(default="", validation_alias="KAFKA_EMBEDDING_TOPIC_NAME")
    num_consumers: int = Field(default=1, validation_alias="KAFKA_NUM_CONSUMERS")
    ollama_host: str = Field(default="", validation_alias="OLLAMA_HOST")
    langfuse_host: str = Field(default="", validation_alias="LANGFUSE_BASE_URL")
    langfuse_public_key: str = Field(default="", validation_alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", validation_alias="LANGFUSE_SECRET_KEY")


_logger: logging.Logger = logging.getLogger("ext_agent_options")

_ext_agent_options: ExtractionAgentOptions | None = None


def get_ext_agent_options() -> ExtractionAgentOptions:
    """Get the singleton instance of ExtractionAgentOptions.

    Returns:
        ExtractionAgentOptions: The application options instance.
    """
    global _ext_agent_options
    if _ext_agent_options is None:
        _ext_agent_options = ExtractionAgentOptions()

        # Validate required configuration
        if not _ext_agent_options.bootstrap_servers:
            raise ValueError("KAFKA_BOOTSTRAP_SERVERS environment variable is required")
        if not _ext_agent_options.consumer_group:
            raise ValueError("KAFKA_CONSUMER_GROUP environment variable is required")
        if not _ext_agent_options.extraction_topic_name:
            raise ValueError("KAFKA_EXTRACTION_TOPIC_NAME environment variable is required")
        if not _ext_agent_options.embedding_topic_name:
            raise ValueError("KAFKA_EMBEDDING_TOPIC_NAME environment variable is required")
        if not _ext_agent_options.num_consumers or _ext_agent_options.num_consumers < 1:
            raise ValueError("KAFKA_NUM_CONSUMERS environment variable must be a positive integer")
        if not _ext_agent_options.ollama_host:
            raise ValueError("OLLAMA_HOST environment variable is required")
        if _ext_agent_options.langfuse_host:
            if not _ext_agent_options.langfuse_public_key:
                raise ValueError("LANGFUSE_PUBLIC_KEY environment variable is required when LANGFUSE_BASE_URL is set")
            if not _ext_agent_options.langfuse_secret_key:
                raise ValueError("LANGFUSE_SECRET_KEY environment variable is required when LANGFUSE_BASE_URL is set")

        _logger.info("Extraction agent options loaded successfully.")

    return _ext_agent_options


def clear_ext_agent_options_cache() -> None:
    """Clear the cached options instance. Useful for testing."""
    global _ext_agent_options
    _ext_agent_options = None
