import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from cocktails_extraction_agent.application.concerns.extraction.commands.process_extraction_event_command import (
    ProcessExtractionEventCommand,
    ProcessExtractionEventCommandHandler,
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
            resolve_ingredients=True,
            measurement_system="imperial",
        )
        llm_content_cleaner.clean_content.assert_awaited_once_with("adonis")
        kafka_producer.send_and_wait.assert_called_once()
        assert handler.cocktail_process_log["adonis"] == datetime(2026, 6, 14, tzinfo=timezone.utc)

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
        handler.cocktail_process_log["adonis"] = modified_on

        command = ProcessExtractionEventCommand(
            CocktailModel.model_construct(
                id="adonis",
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
        handler.cocktail_process_log["adonis"] = datetime(2026, 6, 14, tzinfo=timezone.utc)

        command = ProcessExtractionEventCommand(
            CocktailModel.model_construct(
                id="adonis",
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
        assert handler.cocktail_process_log["adonis"] == newer_modified_on
