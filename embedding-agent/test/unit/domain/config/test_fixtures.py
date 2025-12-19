from typing import Dict, Generator

import pytest


@pytest.fixture
def mock_env_vars() -> Dict[str, str]:
    """Fixture to provide mock environment variables.

    Returns:
        Dict[str, str]: A dictionary of mock environment variables.
    """
    return {
        "EMBEDDING_AGENT_KAFKA_TOPIC_NAME": "test-topic-emb",
        "EMBEDDING_AGENT_KAFKA_NUM_CONSUMERS": "1",
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KAFKA_CONSUMER_GROUP": "test-consumer-group",
        "extra": "value",
    }


@pytest.fixture
def clear_settings_cache() -> Generator[None, None, None]:
    """Clear the settings module cache before each test."""
    from cocktails_embedding_agent.domain.config.emb_agent_options import clear_emb_agent_options_cache
    from cocktails_embedding_agent.domain.config.kafka_options import clear_kafka_options_cache

    # Clear the cached settings before test
    clear_emb_agent_options_cache()
    clear_kafka_options_cache()

    yield

    # Clear the cached settings after test
    clear_emb_agent_options_cache()
    clear_kafka_options_cache()
