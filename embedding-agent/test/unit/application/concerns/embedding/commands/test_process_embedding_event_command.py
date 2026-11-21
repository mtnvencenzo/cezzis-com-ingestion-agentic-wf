import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from cocktails_embedding_agent.application.concerns.embedding.commands.process_embedding_event_command import (
    ProcessEmbeddingEventCommand,
    ProcessEmbeddingEventCommandHandler,
    ProcessEmbeddingEventCommandValidator,
)
from cocktails_embedding_agent.domain.config import AppOptions
from cocktails_embedding_agent.domain.models.cocktail_chunking_model import (
    CocktailChunkingModel,
    CocktailDescriptionChunk,
)
from cocktails_embedding_agent.infrastructure.clients.cocktails_api.cocktails_models import CocktailModel


def _chunking_model(locale) -> CocktailChunkingModel:
    cocktail_model = CocktailModel.model_construct(
        id="adonis",
        locale=locale,
        title="Adonis",
        descriptiveTitle="Adonis Cocktail",
        serves=1,
        prepTimeMinutes=2,
        isIba=False,
        ingredients=[],
        glassware=["Cocktail Glass"],
        rating=SimpleNamespace(rating=4.5),
        images=[],
        keywords=None,
    )
    return CocktailChunkingModel(
        cocktail_model=cocktail_model,
        chunks=[CocktailDescriptionChunk(category="other", content="Ein Klassiker.")],
    )


class TestProcessEmbeddingEventCommand:
    @pytest.mark.parametrize("locale", ["", "  ", None])
    def test_validator_rejects_a_cocktail_without_a_locale(self, locale) -> None:
        command = ProcessEmbeddingEventCommand(_chunking_model(locale))

        with pytest.raises(ValueError, match="no locale"):
            ProcessEmbeddingEventCommandValidator().handle(command, lambda: True)

    def test_handle_sends_the_cocktail_locale_to_the_ai_search_embedding_endpoint(self) -> None:
        aisearch_client = Mock()
        aisearch_client.create_embeddings = AsyncMock(return_value=True)
        consumer_settings = SimpleNamespace(bootstrap_servers="localhost:9092")
        handler = ProcessEmbeddingEventCommandHandler(
            consumer_settings,
            AppOptions.model_construct(consumer_topic_name="embedding-topic"),
            consumer_settings,
            aisearch_client,
        )

        result = asyncio.run(handler.handle(ProcessEmbeddingEventCommand(_chunking_model("de"))))

        assert result is True
        embedding_rq = aisearch_client.create_embeddings.await_args.args[0]
        assert embedding_rq.locale == "de"
        assert embedding_rq.contentChunks[0].content == "Ein Klassiker."
