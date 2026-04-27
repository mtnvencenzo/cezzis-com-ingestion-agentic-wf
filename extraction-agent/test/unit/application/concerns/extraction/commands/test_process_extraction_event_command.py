import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from cocktails_extraction_agent.application.concerns.extraction.commands.process_extraction_event_command import (
    ProcessExtractionEventCommand,
    ProcessExtractionEventCommandHandler,
)


class TestProcessExtractionEventCommandHandler:
    def test_handle_uses_cocktail_id_for_llm_cleaning(self) -> None:
        app_options = SimpleNamespace(use_llm=True, results_topic_name="results-topic")
        kafka_producer = Mock()
        kafka_producer.settings = SimpleNamespace(bootstrap_servers="localhost:9092")
        kafka_producer.send_and_wait = Mock()
        llm_content_cleaner = Mock()
        llm_content_cleaner.clean_content = AsyncMock(return_value="Cleaned content")

        handler = ProcessExtractionEventCommandHandler(app_options, kafka_producer, llm_content_cleaner)
        cocktail_model = SimpleNamespace(
            id="adonis",
            content="## Title",
            title="Adonis",
            descriptiveTitle="Adonis Cocktail",
            description="desc",
        )
        cocktail_model.model_dump = lambda: {
            "id": "adonis",
            "content": "## Title",
            "title": "Adonis",
            "descriptiveTitle": "Adonis Cocktail",
            "description": "desc",
        }
        command = ProcessExtractionEventCommand(cocktail_model)

        result = asyncio.run(handler.handle(command))

        assert result is True
        llm_content_cleaner.clean_content.assert_awaited_once_with("adonis")
        kafka_producer.send_and_wait.assert_called_once()
