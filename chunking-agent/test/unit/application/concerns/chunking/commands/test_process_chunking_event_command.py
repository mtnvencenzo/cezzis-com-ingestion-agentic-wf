import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from cocktails_chunking_agent.application.concerns.chunking.commands.process_chunking_event_command import (
    ProcessChunkingEventCommand,
    ProcessChunkingEventCommandHandler,
    ProcessChunkingEventCommandValidator,
)
from cocktails_chunking_agent.domain.config.app_options import AppOptions
from cocktails_chunking_agent.domain.models.cocktail_chunking_model import CocktailDescriptionChunk
from cocktails_chunking_agent.domain.models.cocktail_extraction_model import CocktailExtractionModel
from cocktails_chunking_agent.infrastructure.clients.cocktails_api.cocktail_api import CocktailModel


class TestProcessChunkingEventCommand:
    @pytest.mark.parametrize("locale", ["", "  ", None])
    def test_validator_rejects_a_cocktail_without_a_locale(self, locale) -> None:
        command = ProcessChunkingEventCommand(
            CocktailExtractionModel(
                extraction_text="Ein Klassiker.",
                cocktail_model=CocktailModel.model_construct(id="adonis", locale=locale),
            )
        )

        with pytest.raises(ValueError, match="no locale"):
            ProcessChunkingEventCommandValidator().handle(command, lambda: True)

    def test_handle_chunks_in_the_cocktail_locale_and_forwards_the_locale(self) -> None:
        kafka_producer = Mock()
        llm_content_chunker = Mock()
        llm_content_chunker.chunk_content = AsyncMock(
            return_value=[CocktailDescriptionChunk(category="other", content="Ein Klassiker.")]
        )
        handler = ProcessChunkingEventCommandHandler(
            kafka_producer,
            AppOptions.model_construct(results_topic_name="results-topic"),
            SimpleNamespace(bootstrap_servers="localhost:9092"),
            llm_content_chunker,
        )
        cocktail_model = CocktailModel.model_construct(id="adonis", locale="de")

        with patch.object(CocktailModel, "model_dump", return_value={"id": "adonis", "locale": "de"}):
            result = asyncio.run(
                handler.handle(
                    ProcessChunkingEventCommand(
                        CocktailExtractionModel(extraction_text="Ein Klassiker.", cocktail_model=cocktail_model)
                    )
                )
            )

        assert result is True
        llm_content_chunker.chunk_content.assert_awaited_once_with(
            cocktail_id="adonis", locale="de", extraction_text="Ein Klassiker."
        )
        sent = kafka_producer.send_and_wait.call_args.kwargs["message"]
        assert b'"locale":"de"' in sent
