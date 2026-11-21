import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from cocktails_extraction_agent.application.concerns.extraction.commands.process_extraction_event_command import (
    ProcessExtractionEventCommand,
    ProcessExtractionEventCommandHandler,
    ProcessExtractionEventCommandValidator,
)
from cocktails_extraction_agent.domain.config.app_options import AppOptions
from cocktails_extraction_agent.infrastructure.clients.cocktails_api.cocktail_api import CocktailModel


class TestProcessExtractionEventCommandHandler:
    def test_handle_uses_cocktail_id_for_llm_cleaning(self) -> None:
        app_options = AppOptions.model_construct(
            use_llm=True,
            results_topic_name="results-topic",
        )
        kafka_producer = Mock()
        kafka_producer.settings = SimpleNamespace(bootstrap_servers="localhost:9092")
        kafka_producer.send_and_wait = Mock()
        llm_content_cleaner = Mock()
        llm_content_cleaner.clean_content = AsyncMock(return_value="Cleaned content")
        cocktails_api_service = Mock()

        latest_cocktail_model = CocktailModel.model_construct(
            id="adonis",
            locale="en",
            content="## Refreshed Title",
            title="Adonis",
            descriptiveTitle="Adonis Cocktail",
            description="desc",
            modifiedOn=datetime(2026, 6, 14, tzinfo=timezone.utc),
        )
        cocktails_api_service.get_cocktail = AsyncMock(return_value=latest_cocktail_model)

        handler = ProcessExtractionEventCommandHandler(
            app_options,
            kafka_producer,
            llm_content_cleaner,
            cocktails_api_service,
        )
        cocktail_model = CocktailModel.model_construct(
            id="adonis",
            locale="en",
            content="## Stale Title",
            title="Adonis",
            descriptiveTitle="Adonis Cocktail",
            description="desc",
            modifiedOn=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        command = ProcessExtractionEventCommand(cocktail_model)

        result = asyncio.run(handler.handle(command))

        assert result is True
        cocktails_api_service.get_cocktail.assert_awaited_once_with(
            id="adonis",
            locale="en",
            resolve_ingredients=True,
            measurement_system="imperial",
        )
        llm_content_cleaner.clean_content.assert_awaited_once_with("adonis", "en")
        kafka_producer.send_and_wait.assert_called_once()
        assert handler.cocktail_process_log[("adonis", "en")] == datetime(2026, 6, 14, tzinfo=timezone.utc)

    def test_handle_skips_already_processed_modified_on(self) -> None:
        app_options = AppOptions.model_construct(
            use_llm=True,
            results_topic_name="results-topic",
        )
        kafka_producer = Mock()
        kafka_producer.settings = SimpleNamespace(bootstrap_servers="localhost:9092")
        kafka_producer.send_and_wait = Mock()
        llm_content_cleaner = Mock()
        llm_content_cleaner.clean_content = AsyncMock(return_value="Cleaned content")
        cocktails_api_service = Mock()

        modified_on = datetime(2026, 6, 14, tzinfo=timezone.utc)
        latest_cocktail_model = CocktailModel.model_construct(
            id="adonis",
            locale="en",
            content="## Refreshed Title",
            title="Adonis",
            descriptiveTitle="Adonis Cocktail",
            description="desc",
            modifiedOn=modified_on,
        )
        cocktails_api_service.get_cocktail = AsyncMock(return_value=latest_cocktail_model)

        handler = ProcessExtractionEventCommandHandler(
            app_options,
            kafka_producer,
            llm_content_cleaner,
            cocktails_api_service,
        )
        # Simulate that this cocktail version was already processed and sent.
        handler.cocktail_process_log[("adonis", "en")] = modified_on

        command = ProcessExtractionEventCommand(
            CocktailModel.model_construct(
                id="adonis",
                locale="en",
                content="## Stale Title",
                title="Adonis",
                descriptiveTitle="Adonis Cocktail",
                description="desc",
                modifiedOn=datetime(2026, 6, 1, tzinfo=timezone.utc),
            )
        )

        result = asyncio.run(handler.handle(command))

        assert result is True
        cocktails_api_service.get_cocktail.assert_awaited_once_with(
            id="adonis",
            locale="en",
            resolve_ingredients=True,
            measurement_system="imperial",
        )
        llm_content_cleaner.clean_content.assert_not_awaited()
        kafka_producer.send_and_wait.assert_not_called()

    def test_handle_processes_newer_modified_on(self) -> None:
        app_options = AppOptions.model_construct(
            use_llm=True,
            results_topic_name="results-topic",
        )
        kafka_producer = Mock()
        kafka_producer.settings = SimpleNamespace(bootstrap_servers="localhost:9092")
        kafka_producer.send_and_wait = Mock()
        llm_content_cleaner = Mock()
        llm_content_cleaner.clean_content = AsyncMock(return_value="Cleaned content")
        cocktails_api_service = Mock()

        newer_modified_on = datetime(2026, 6, 20, tzinfo=timezone.utc)
        latest_cocktail_model = CocktailModel.model_construct(
            id="adonis",
            locale="en",
            content="## Refreshed Title",
            title="Adonis",
            descriptiveTitle="Adonis Cocktail",
            description="desc",
            modifiedOn=newer_modified_on,
        )
        cocktails_api_service.get_cocktail = AsyncMock(return_value=latest_cocktail_model)

        handler = ProcessExtractionEventCommandHandler(
            app_options,
            kafka_producer,
            llm_content_cleaner,
            cocktails_api_service,
        )
        # An older version was previously processed; a newer version should be sent.
        handler.cocktail_process_log[("adonis", "en")] = datetime(2026, 6, 14, tzinfo=timezone.utc)

        command = ProcessExtractionEventCommand(
            CocktailModel.model_construct(
                id="adonis",
                locale="en",
                content="## Stale Title",
                title="Adonis",
                descriptiveTitle="Adonis Cocktail",
                description="desc",
                modifiedOn=datetime(2026, 6, 1, tzinfo=timezone.utc),
            )
        )

        result = asyncio.run(handler.handle(command))

        assert result is True
        kafka_producer.send_and_wait.assert_called_once()
        assert handler.cocktail_process_log[("adonis", "en")] == newer_modified_on

    def test_handle_fetches_and_processes_each_locale_separately(self) -> None:
        app_options = AppOptions.model_construct(use_llm=True, results_topic_name="results-topic")
        kafka_producer = Mock()
        kafka_producer.settings = SimpleNamespace(bootstrap_servers="localhost:9092")
        kafka_producer.send_and_wait = Mock()
        llm_content_cleaner = Mock()
        llm_content_cleaner.clean_content = AsyncMock(return_value="Bereinigter Inhalt")
        cocktails_api_service = Mock()

        modified_on = datetime(2026, 6, 14, tzinfo=timezone.utc)
        cocktails_api_service.get_cocktail = AsyncMock(
            return_value=CocktailModel.model_construct(
                id="adonis", locale="de", content="## Titel", title="Adonis", modifiedOn=modified_on
            )
        )

        handler = ProcessExtractionEventCommandHandler(
            app_options, kafka_producer, llm_content_cleaner, cocktails_api_service
        )
        # The English version was already processed; the German one must still be processed.
        handler.cocktail_process_log[("adonis", "en")] = modified_on

        result = asyncio.run(
            handler.handle(
                ProcessExtractionEventCommand(
                    CocktailModel.model_construct(id="adonis", locale="de", content="", modifiedOn=modified_on)
                )
            )
        )

        assert result is True
        assert cocktails_api_service.get_cocktail.await_args.kwargs["locale"] == "de"
        llm_content_cleaner.clean_content.assert_awaited_once_with("adonis", "de")
        kafka_producer.send_and_wait.assert_called_once()
        assert handler.cocktail_process_log[("adonis", "de")] == modified_on

    def test_handle_rejects_content_returned_in_a_different_language(self) -> None:
        app_options = AppOptions.model_construct(use_llm=True, results_topic_name="results-topic")
        kafka_producer = Mock()
        llm_content_cleaner = Mock()
        llm_content_cleaner.clean_content = AsyncMock(return_value="Cleaned content")
        cocktails_api_service = Mock()
        cocktails_api_service.get_cocktail = AsyncMock(
            return_value=CocktailModel.model_construct(
                id="adonis",
                locale="en",
                content="## Title",
                modifiedOn=datetime(2026, 6, 14, tzinfo=timezone.utc),
            )
        )

        handler = ProcessExtractionEventCommandHandler(
            app_options, kafka_producer, llm_content_cleaner, cocktails_api_service
        )

        with pytest.raises(ValueError, match="'de' was requested"):
            asyncio.run(
                handler.handle(
                    ProcessExtractionEventCommand(
                        CocktailModel.model_construct(id="adonis", locale="de", content="", modifiedOn=None)
                    )
                )
            )

        llm_content_cleaner.clean_content.assert_not_awaited()
        kafka_producer.send_and_wait.assert_not_called()


class TestProcessExtractionEventCommandValidator:
    @pytest.mark.parametrize("locale", ["", "  ", None])
    def test_rejects_a_cocktail_without_a_locale(self, locale) -> None:
        command = ProcessExtractionEventCommand(CocktailModel.model_construct(id="adonis", locale=locale))

        with pytest.raises(ValueError, match="no locale"):
            ProcessExtractionEventCommandValidator().handle(command, lambda: True)
