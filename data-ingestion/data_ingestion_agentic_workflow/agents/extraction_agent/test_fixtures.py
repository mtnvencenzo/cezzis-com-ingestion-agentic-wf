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
