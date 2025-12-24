from typing import Dict, Generator

import pytest


@pytest.fixture
def mock_env_vars() -> Dict[str, str]:
    """Fixture to provide mock environment variables.

    Returns:
        Dict[str, str]: A dictionary of mock environment variables.
    """
    return {
        "EXTRACTION_AGENT_KAFKA_TOPIC_NAME": "test-topic-ext",
        "EXTRACTION_AGENT_KAFKA_NUM_CONSUMERS": "1",
        "EXTRACTION_AGENT_KAFKA_RESULTS_TOPIC_NAME": "test-topic-results",
        "EXTRACTION_AGENT_MODEL": "hermes3-llama3.2:3b Q3_K_S",
        "LLM_HOST": "http://localhost:11000",
        "LANGFUSE_SECRET_KEY": "sk-lf-",
        "LANGFUSE_PUBLIC_KEY": "pk-lf-",
        "LANGFUSE_BASE_URL": "https://localhost:8080",
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KAFKA_CONSUMER_GROUP": "test-consumer-group",
        "extra": "value",
    }


@pytest.fixture
def clear_settings_cache() -> Generator[None, None, None]:
    """Clear the settings module cache before each test."""
    from cocktails_extraction_agent.domain.config.app_options import clear_app_options_cache
    from cocktails_extraction_agent.domain.config.kafka_options import clear_kafka_options_cache
    from cocktails_extraction_agent.domain.config.llm_options import clear_llm_options_cache

    # Clear the cached settings before test
    clear_app_options_cache()
    clear_kafka_options_cache()
    clear_llm_options_cache()

    yield

    # Clear the cached settings after test
    clear_app_options_cache()
    clear_kafka_options_cache()
    clear_llm_options_cache()
