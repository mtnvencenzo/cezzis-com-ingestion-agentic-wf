import asyncio
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
            cocktail_reprocess_cooldown_seconds=180,
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
