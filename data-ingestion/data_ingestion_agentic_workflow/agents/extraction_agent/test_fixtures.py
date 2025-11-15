from typing import Dict, Generator

import pytest


@pytest.fixture
def mock_env_vars() -> Dict[str, str]:
    """Fixture to provide mock environment variables.

    Returns:
        Dict[str, str]: A dictionary of mock environment variables.
    """
    return {
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KAFKA_CONSUMER_GROUP": "test-consumer-group",
        "KAFKA_EXTRACTION_TOPIC_NAME": "test-topic-ext",
        "KAFKA_EMBEDDING_TOPIC_NAME": "test-topic-emb",
        "KAFKA_NUM_CONSUMERS": "1",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4316",
        "OTEL_SERVICE_NAME": "test-service",
        "OTEL_SERVICE_NAMESPACE": "test-namespace",
        "OTEL_OTLP_AUTH_HEADER": "Bearer test-token",
        "OLLAMA_HOST": "http://localhost:11434",
    }


@pytest.fixture
def clear_settings_cache() -> Generator[None, None, None]:
    """Clear the settings module cache before each test."""
    from data_ingestion_agentic_workflow.agents.extraction_agent.ext_agent_options import clear_ext_agent_options_cache

    # Clear the cached settings before test
    clear_ext_agent_options_cache()

    yield

    # Clear the cached settings after test
    clear_ext_agent_options_cache()
