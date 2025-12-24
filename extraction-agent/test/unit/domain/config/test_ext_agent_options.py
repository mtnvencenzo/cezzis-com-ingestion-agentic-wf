"""Unit tests for app_settings module."""

from typing import Any, Dict, Generator

import pytest
from pytest_mock import MockerFixture

from cocktails_extraction_agent.domain.config.app_options import (
    AppOptions,
    get_app_options,
)

from .test_fixtures import (  # type: ignore[import]
    clear_settings_cache,
    mock_env_vars,
)


class TestAppOptions:
    @pytest.mark.usefixtures("clear_settings_cache")
    def test_ext_agent_settings_loads_from_environment_variables(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.dict("os.environ", mock_env_vars)
        mocker.patch("builtins.print")

        options_instance = get_app_options()

        assert options_instance.consumer_topic_name == "test-topic-ext"
        assert options_instance.results_topic_name == "test-topic-results"
        assert options_instance.num_consumers == 1
        assert options_instance.enabled is True

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_raises_error_when_consumer_topic_name_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Any,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.dict(
            "os.environ",
            {key: value for key, value in mock_env_vars.items() if key != "EXTRACTION_AGENT_KAFKA_TOPIC_NAME"},
            clear=True,
        )

        with pytest.raises(ValueError, match="EXTRACTION_AGENT_KAFKA_TOPIC_NAME.*required"):
            get_app_options()

    @pytest.mark.usefixtures("clear_settings_cache")
    @pytest.mark.parametrize("num_consumers", ["0", "-1"])
    def test_settings_raises_error_when_num_consumers_is_less_than_one(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Any,
        mocker: MockerFixture,
        num_consumers: str,
    ) -> None:
        mocker.patch.dict(
            "os.environ",
            {
                **{k: v for k, v in mock_env_vars.items() if k != "EXTRACTION_AGENT_KAFKA_NUM_CONSUMERS"},
                "EXTRACTION_AGENT_KAFKA_NUM_CONSUMERS": num_consumers,
            },
            clear=True,
        )

        with pytest.raises(ValueError, match="EXTRACTION_AGENT_KAFKA_NUM_CONSUMERS.*positive integer"):
            get_app_options()

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_raises_error_when_results_topic_name_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Any,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.dict(
            "os.environ",
            {key: value for key, value in mock_env_vars.items() if key != "EXTRACTION_AGENT_KAFKA_RESULTS_TOPIC_NAME"},
            clear=True,
        )

        with pytest.raises(ValueError, match="EXTRACTION_AGENT_KAFKA_RESULTS_TOPIC_NAME.*required"):
            get_app_options()

    def test_settings_raises_error_when_model_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Any,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.dict(
            "os.environ",
            {key: value for key, value in mock_env_vars.items() if key != "EXTRACTION_AGENT_LLM_MODEL"},
            clear=True,
        )

        with pytest.raises(ValueError, match="EXTRACTION_AGENT_LLM_MODEL.*required"):
            get_app_options()

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_with_env_file(
        self, clear_settings_cache: Generator[None, None, None], mocker: MockerFixture, tmp_path: Any
    ) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text(
            "EXTRACTION_AGENT_ENABLED=true\n"
            "EXTRACTION_AGENT_KAFKA_TOPIC_NAME=file-topic-ext\n"
            "EXTRACTION_AGENT_KAFKA_RESULTS_TOPIC_NAME=file-topic-results\n"
            "EXTRACTION_AGENT_KAFKA_NUM_CONSUMERS=2\n"
            "EXTRACTION_AGENT_LLM_MODEL=hermes3-llama3.2:3b Q3_K_S\n"
            "EXTRA_VAR=extra-value\n"  # good for testing pydantics extra="allow" feature
        )

        mocker.patch.dict("os.environ", {"ENV": ""}, clear=True)
        mocker.patch("builtins.print")

        # Change to the temp directory
        import os

        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            settings = AppOptions()

            assert settings.enabled is True
            assert settings.consumer_topic_name == "file-topic-ext"
            assert settings.results_topic_name == "file-topic-results"
            assert settings.num_consumers == 2
            assert settings.llm_model == "hermes3-llama3.2:3b Q3_K_S"
        finally:
            os.chdir(original_dir)

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_model_config(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.dict("os.environ", mock_env_vars)
        mocker.patch("builtins.print")

        # Verify the model has the expected configuration
        assert AppOptions.model_config is not None
        assert "env_file" in AppOptions.model_config
        assert AppOptions.model_config.get("env_file_encoding") == "utf-8"
