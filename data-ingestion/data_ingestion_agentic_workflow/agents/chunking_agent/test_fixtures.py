from typing import Dict, Generator

import pytest


@pytest.fixture
def mock_env_vars() -> Dict[str, str]:
    """Fixture to provide mock environment variables.

    Returns:
        Dict[str, str]: A dictionary of mock environment variables.
    """
    return {
        "CHUNKING_AGENT_KAFKA_TOPIC_NAME": "test-topic-extraction",
        "CHUNKING_AGENT_KAFKA_NUM_CONSUMERS": "1",
        "CHUNKING_AGENT_KAFKA_RESULTS_TOPIC_NAME": "test-topic-results",
        "CHUNKING_AGENT_LLM_MODEL": "qwen3:8b",
    }


@pytest.fixture
def clear_settings_cache() -> Generator[None, None, None]:
    """Clear the settings module cache before each test."""
    from data_ingestion_agentic_workflow.agents.chunking_agent.chunking_agent_options import (
        clear_chunking_agent_options_cache,
    )

    # Clear the cached settings before test
    clear_chunking_agent_options_cache()

    yield

    # Clear the cached settings after test
    clear_chunking_agent_options_cache()
