"""Unit tests for app_settings module."""

from typing import Any, Dict, Generator

import pytest
from pytest_mock import MockerFixture

from data_ingestion_agentic_workflow.agents.extraction_agent.test_fixtures import (  # type: ignore[import]
    clear_settings_cache,
    mock_env_vars,
)


class TestExtractionAgentOptions:
    """Test suite for ExtractionAgentOptions configuration."""

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_ext_agent_settings_loads_from_environment_variables(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        """Test that settings are correctly loaded from environment variables."""
        mocker.patch.dict("os.environ", mock_env_vars)
        mocker.patch("builtins.print")  # Suppress print output

        from data_ingestion_agentic_workflow.agents.extraction_agent.ext_agent_options import get_ext_agent_options

        # Call the function to get the settings instance
        options_instance = get_ext_agent_options()

        assert options_instance.bootstrap_servers == "localhost:9092"
        assert options_instance.consumer_group == "test-consumer-group"
        assert options_instance.extraction_topic_name == "test-topic-ext"
        assert options_instance.embedding_topic_name == "test-topic-emb"
        assert options_instance.ollama_host == "http://localhost:11434"
        assert options_instance.num_consumers == 1

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_raises_error_when_bootstrap_servers_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        """Test that missing KAFKA_BOOTSTRAP_SERVERS raises ValueError."""
        mocker.patch.dict(
            "os.environ",
            {key: value for key, value in mock_env_vars.items() if key != "KAFKA_BOOTSTRAP_SERVERS"},
            clear=True,
        )

        with pytest.raises(ValueError, match="KAFKA_BOOTSTRAP_SERVERS.*required"):
            from data_ingestion_agentic_workflow.agents.extraction_agent.ext_agent_options import get_ext_agent_options

            get_ext_agent_options()  # type: ignore[unused-ignore]

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_raises_error_when_consumer_group_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        """Test that missing KAFKA_CONSUMER_GROUP raises ValueError."""
        mocker.patch.dict(
            "os.environ",
            {key: value for key, value in mock_env_vars.items() if key != "KAFKA_CONSUMER_GROUP"},
            clear=True,
        )

        with pytest.raises(ValueError, match="KAFKA_CONSUMER_GROUP.*required"):
            from data_ingestion_agentic_workflow.agents.extraction_agent.ext_agent_options import get_ext_agent_options

            get_ext_agent_options()  # type: ignore[unused-ignore]

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_raises_error_when_extraction_topic_name_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Any,
        mocker: MockerFixture,
    ) -> None:
        """Test that missing KAFKA_TOPIC_NAME raises ValueError."""
        mocker.patch.dict(
            "os.environ",
            {key: value for key, value in mock_env_vars.items() if key != "KAFKA_EXTRACTION_TOPIC_NAME"},
            clear=True,
        )

        with pytest.raises(ValueError, match="KAFKA_EXTRACTION_TOPIC_NAME.*required"):
            from data_ingestion_agentic_workflow.agents.extraction_agent.ext_agent_options import get_ext_agent_options

            get_ext_agent_options()  # type: ignore[unused-ignore]

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_raises_error_when_ollama_host_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Any,
        mocker: MockerFixture,
    ) -> None:
        """Test that missing OLLAMA_HOST raises ValueError."""
        mocker.patch.dict(
            "os.environ",
            {key: value for key, value in mock_env_vars.items() if key != "OLLAMA_HOST"},
            clear=True,
        )

        with pytest.raises(ValueError, match="OLLAMA_HOST.*required"):
            from data_ingestion_agentic_workflow.agents.extraction_agent.ext_agent_options import get_ext_agent_options

            get_ext_agent_options()  # type: ignore[unused-ignore]

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_with_env_file(
        self, clear_settings_cache: Generator[None, None, None], mocker: MockerFixture, tmp_path: Any
    ) -> None:
        """Test that settings can be loaded from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "KAFKA_BOOTSTRAP_SERVERS=localhost:9092\n"
            "KAFKA_CONSUMER_GROUP=file-consumer-group\n"
            "KAFKA_EXTRACTION_TOPIC_NAME=file-topic-ext\n"
            "KAFKA_EMBEDDING_TOPIC_NAME=file-topic-emb\n"
            "KAFKA_NUM_CONSUMERS=2\n"
            "OLLAMA_HOST=http://localhost:11434\n"
            "EXTRA_VAR=extra-value\n"  # good for testing pydantics extra="allow" feature
        )

        mocker.patch.dict("os.environ", {"ENV": ""}, clear=True)
        mocker.patch("builtins.print")

        # Change to the temp directory
        import os

        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            from data_ingestion_agentic_workflow.agents.extraction_agent.ext_agent_options import ExtractionAgentOptions

            settings = ExtractionAgentOptions()

            assert settings.bootstrap_servers == "localhost:9092"
            assert settings.consumer_group == "file-consumer-group"
            assert settings.extraction_topic_name == "file-topic-ext"
            assert settings.embedding_topic_name == "file-topic-emb"
            assert settings.ollama_host == "http://localhost:11434"
            assert settings.num_consumers == 2
        finally:
            os.chdir(original_dir)

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_model_config(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        """Test that AppSettings has correct model configuration."""
        mocker.patch.dict("os.environ", mock_env_vars)
        mocker.patch("builtins.print")

        from data_ingestion_agentic_workflow.agents.extraction_agent.ext_agent_options import ExtractionAgentOptions

        # Verify the model has the expected configuration
        assert ExtractionAgentOptions.model_config is not None
        assert "env_file" in ExtractionAgentOptions.model_config
        assert ExtractionAgentOptions.model_config.get("env_file_encoding") == "utf-8"
