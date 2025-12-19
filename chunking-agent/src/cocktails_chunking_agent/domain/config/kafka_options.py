import logging
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaOptions(BaseSettings):
    """Kafka configuration options loaded from environment variables and .env files.

    Attributes:
        bootstrap_servers (str): Kafka bootstrap servers.
        consumer_group (str): Kafka consumer group ID.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{os.environ.get('ENV')}"), env_file_encoding="utf-8", extra="allow"
    )

    bootstrap_servers: str = Field(default="", validation_alias="KAFKA_BOOTSTRAP_SERVERS")
    consumer_group: str = Field(default="", validation_alias="KAFKA_CONSUMER_GROUP")


_logger: logging.Logger = logging.getLogger("kafka_options")

_kafka_options: KafkaOptions | None = None


def get_kafka_options() -> KafkaOptions:
    """Get the singleton instance of KafkaOptions.

    Returns:
        KafkaOptions: The Kafka options instance.
    """
    global _kafka_options
    if _kafka_options is None:
        _kafka_options = KafkaOptions()

        # Validate required configuration
        if not _kafka_options.bootstrap_servers:
            raise ValueError("KAFKA_BOOTSTRAP_SERVERS environment variable is required")
        if not _kafka_options.consumer_group:
            raise ValueError("KAFKA_CONSUMER_GROUP environment variable is required")

        _logger.info("Kafka options loaded successfully.")

    return _kafka_options


def clear_kafka_options_cache() -> None:
    """Clear the cached KafkaOptions instance."""
    global _kafka_options
    _kafka_options = None
