import logging
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppOptions(BaseSettings):
    """Application settings loaded from environment variables and .env files.

    Attributes:
        enabled (bool): Flag to enable or disable the chunking agent.
        consumer_topic_name (str): Kafka chunking topic name.
        results_topic_name (str): Kafka results topic name.
        num_consumers (int): Number of Kafka consumer processes to start.
        max_poll_interval_ms (int): Maximum poll interval in milliseconds.
        auto_offset_reset (str): Kafka auto offset reset policy.
        llm_model (str): The LLM model to use for chunking.
        llm_model_temperature (float): Temperature setting for the LLM model.
        llm_model_num_ctx (int): Number of context tokens for the LLM model.
        llm_model_disable_streaming (bool): Whether to disable streaming for the LLM model.
        llm_model_num_predict (int): Number of tokens to predict for the LLM model.
        llm_model_log_verbose (bool): Whether to enable verbose logging for the LLM model.
        llm_model_timeout_seconds (int): Timeout in seconds for LLM model execution.
        llm_model_reasoning (bool): Whether to enable reasoning mode for the LLM model.
        log_dir (str): Directory to store log files.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{os.environ.get('ENV')}"), env_file_encoding="utf-8", extra="allow"
    )

    enabled: bool = Field(default=True, validation_alias="CHUNKING_AGENT_ENABLED")
    consumer_topic_name: str = Field(default="", validation_alias="CHUNKING_AGENT_KAFKA_TOPIC_NAME")
    num_consumers: int = Field(default=1, validation_alias="CHUNKING_AGENT_KAFKA_NUM_CONSUMERS")
    max_poll_interval_ms: int = Field(default=300000, validation_alias="CHUNKING_AGENT_KAFKA_MAX_POLL_INTERVAL_MS")
    auto_offset_reset: str = Field(default="earliest", validation_alias="CHUNKING_AGENT_KAFKA_AUTO_OFFSET_RESET")
    results_topic_name: str = Field(default="", validation_alias="CHUNKING_AGENT_KAFKA_RESULTS_TOPIC_NAME")
    llm_model: str = Field(default="", validation_alias="CHUNKING_AGENT_LLM_MODEL")
    llm_model_temperature: float = Field(default=0.3, validation_alias="CHUNKING_AGENT_LLM_MODEL_TEMPERATURE")
    llm_model_num_ctx: int | None = Field(default=None, validation_alias="CHUNKING_AGENT_LLM_MODEL_NUM_CTX")
    llm_model_disable_streaming: bool = Field(
        default=False, validation_alias="CHUNKING_AGENT_LLM_MODEL_DISABLE_STREAMING"
    )
    llm_model_num_predict: int = Field(default=2048, validation_alias="CHUNKING_AGENT_LLM_MODEL_NUM_PREDICT")
    llm_model_log_verbose: bool = Field(default=False, validation_alias="CHUNKING_AGENT_LLM_MODEL_LOG_VERBOSE")
    llm_model_timeout_seconds: int = Field(
        default=60,
        validation_alias="CHUNKING_AGENT_LLM_MODEL_TIMEOUT_SECONDS",
    )
    llm_model_reasoning: bool = Field(default=False, validation_alias="CHUNKING_AGENT_LLM_MODEL_REASONING")
    log_dir: str = Field(default="", validation_alias="CHUNKING_AGENT_LOG_DIR")


_logger: logging.Logger = logging.getLogger("app_options")

_app_options: AppOptions | None = None


def get_app_options() -> AppOptions:
    """Get the singleton instance of AppOptions.

    Returns:
        AppOptions: The application options instance.
    """
    global _app_options
    if _app_options is None:
        _app_options = AppOptions()

        # Validate required configuration
        if not _app_options.consumer_topic_name:
            raise ValueError("CHUNKING_AGENT_KAFKA_TOPIC_NAME environment variable is required")
        if not _app_options.results_topic_name:
            raise ValueError("CHUNKING_AGENT_KAFKA_RESULTS_TOPIC_NAME environment variable is required")
        if not _app_options.num_consumers or _app_options.num_consumers < 1:
            raise ValueError("CHUNKING_AGENT_KAFKA_NUM_CONSUMERS environment variable must be a positive integer")
        if not _app_options.llm_model:
            raise ValueError("CHUNKING_AGENT_LLM_MODEL environment variable is required")
        if _app_options.llm_model_temperature < 0.0 or _app_options.llm_model_temperature > 1.0:
            raise ValueError("CHUNKING_AGENT_LLM_MODEL_TEMPERATURE environment variable must be between 0.0 and 1.0")
        if _app_options.llm_model_num_ctx and _app_options.llm_model_num_ctx < 1:
            raise ValueError("CHUNKING_AGENT_LLM_MODEL_NUM_CTX environment variable must be a positive integer")
        if _app_options.auto_offset_reset not in ("earliest", "latest", "none"):
            raise ValueError(
                "CHUNKING_AGENT_KAFKA_AUTO_OFFSET_RESET environment variable must be one of: 'earliest', 'latest', 'none'"
            )
        if _app_options.max_poll_interval_ms < 1000:
            raise ValueError(
                "CHUNKING_AGENT_KAFKA_MAX_POLL_INTERVAL_MS environment variable must be at least 1000 milliseconds"
            )

        _logger.info("Chunking agent options loaded successfully.")

    return _app_options


def clear_app_options_cache() -> None:
    """Clear the cached options instance. Useful for testing."""
    global _app_options
    _app_options = None
