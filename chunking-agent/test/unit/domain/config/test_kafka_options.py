from typing import Any, Dict, Generator

import pytest
from pytest_mock import MockerFixture

from cocktails_chunking_agent.domain.config.kafka_options import KafkaOptions, get_kafka_options

from .test_fixtures import (  # type: ignore[import]
    clear_settings_cache,
    mock_env_vars,
)


class TestKafkaOptions:
    @pytest.mark.usefixtures("clear_settings_cache")
    def test_get_kafka_options(
        self, mock_env_vars: Dict[str, str], clear_settings_cache: Generator[None, None, None], mocker: MockerFixture
    ) -> None:
        mocker.patch.dict("os.environ", mock_env_vars)
        mocker.patch("builtins.print")

        kafka_options = get_kafka_options()
        assert kafka_options is not None
        assert kafka_options.bootstrap_servers is not None
        assert kafka_options.consumer_group is not None

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_options_raises_error_when_bootstrap_servers_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.dict(
            "os.environ",
            {key: value for key, value in mock_env_vars.items() if key != "KAFKA_BOOTSTRAP_SERVERS"},
            clear=True,
        )

        with pytest.raises(ValueError, match="KAFKA_BOOTSTRAP_SERVERS.*required"):
            get_kafka_options()  # type: ignore[unused-ignore]

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_options_raises_error_when_consumer_group_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.dict(
            "os.environ",
            {key: value for key, value in mock_env_vars.items() if key != "KAFKA_CONSUMER_GROUP"},
            clear=True,
        )

        with pytest.raises(ValueError, match="KAFKA_CONSUMER_GROUP.*required"):
            get_kafka_options()

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_with_env_file(
        self, clear_settings_cache: Generator[None, None, None], mocker: MockerFixture, tmp_path: Any
    ) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text(
            "KAFKA_BOOTSTRAP_SERVERS=127.0.0.1:90000\n"
            "KAFKA_CONSUMER_GROUP=test-consumer-group\n"
            "EXTRA_VAR=extra-value\n"  # good for testing pydantics extra="allow" feature
        )

        mocker.patch.dict("os.environ", {"ENV": ""}, clear=True)
        mocker.patch("builtins.print")

        # Change to the temp directory
        import os

        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            settings = KafkaOptions()

            assert settings.bootstrap_servers == "127.0.0.1:90000"
            assert settings.consumer_group == "test-consumer-group"
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
        assert KafkaOptions.model_config is not None
        assert "env_file" in KafkaOptions.model_config
        assert KafkaOptions.model_config.get("env_file_encoding") == "utf-8"
