from collections.abc import Generator
from typing import Any, Dict

import pytest
from pytest_mock import MockerFixture

from cocktails_extraction_agent.domain.config.llm_options import LLMOptions, get_llm_options

from .test_fixtures import (  # type: ignore[import]
    clear_settings_cache,
    mock_env_vars,
)


class TestLLMOptions:
    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_loads_from_environment_variables(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.dict("os.environ", mock_env_vars)
        mocker.patch("builtins.print")

        options_instance = get_llm_options()

        assert options_instance.llm_host == "http://localhost:11000"
        assert options_instance.langfuse_secret_key == "sk-lf-"
        assert options_instance.langfuse_public_key == "pk-lf-"
        assert options_instance.langfuse_host == "https://localhost:8080"

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_builds_when_llm_host_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.dict(
            "os.environ",
            {key: value for key, value in mock_env_vars.items() if key != "LLM_HOST"},
            clear=True,
        )

        options_instance = get_llm_options()

        assert options_instance.llm_host is None
        assert options_instance.langfuse_secret_key == "sk-lf-"
        assert options_instance.langfuse_public_key == "pk-lf-"
        assert options_instance.langfuse_host == "https://localhost:8080"

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_loads_when_langfuse_options_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.dict(
            "os.environ",
            {
                key: value
                for key, value in mock_env_vars.items()
                if key != "LANGFUSE_BASE_URL" and key != "LANGFUSE_PUBLIC_KEY" and key != "LANGFUSE_SECRET_KEY"
            },
            clear=True,
        )

        opts = get_llm_options()
        assert opts.llm_host == "http://localhost:11000"
        assert opts.langfuse_host == ""
        assert opts.langfuse_public_key == ""
        assert opts.langfuse_secret_key == ""

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_raises_error_when_langfuse_host_present_but_public_key_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.dict(
            "os.environ",
            {key: value for key, value in mock_env_vars.items() if key != "LANGFUSE_PUBLIC_KEY"},
            clear=True,
        )

        with pytest.raises(ValueError, match="LANGFUSE_PUBLIC_KEY.*required"):
            get_llm_options()

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_raises_error_when_langfuse_host_present_but_secret_key_missing(
        self,
        mock_env_vars: Dict[str, str],
        clear_settings_cache: Generator[None, None, None],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.dict(
            "os.environ",
            {key: value for key, value in mock_env_vars.items() if key != "LANGFUSE_SECRET_KEY"},
            clear=True,
        )

        with pytest.raises(ValueError, match="LANGFUSE_SECRET_KEY.*required"):
            get_llm_options()

    @pytest.mark.usefixtures("clear_settings_cache")
    def test_settings_with_env_file(
        self, clear_settings_cache: Generator[None, None, None], mocker: MockerFixture, tmp_path: Any
    ) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text(
            "LLM_HOST=http://localhost:11000\n"
            "LANGFUSE_BASE_URL=http://localhost:11001\n"
            "LANGFUSE_PUBLIC_KEY=my-pub-key\n"
            "LANGFUSE_SECRET_KEY=my-sec-key\n"
            "EXTRA_VAR=extra-value\n"  # good for testing pydantics extra="allow" feature
        )

        mocker.patch.dict("os.environ", {"ENV": ""}, clear=True)
        mocker.patch("builtins.print")

        # Change to the temp directory
        import os

        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            settings = LLMOptions()

            assert settings.llm_host == "http://localhost:11000"
            assert settings.langfuse_host == "http://localhost:11001"
            assert settings.langfuse_public_key == "my-pub-key"
            assert settings.langfuse_secret_key == "my-sec-key"
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
        assert LLMOptions.model_config is not None
        assert "env_file" in LLMOptions.model_config
        assert LLMOptions.model_config.get("env_file_encoding") == "utf-8"
