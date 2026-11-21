import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import TypeAdapter

from cocktails_embedding_agent.application.concerns.embedding.commands.process_embedding_event_command import (
    ProcessEmbeddingEventCommand,
    ProcessEmbeddingEventCommandHandler,
)
from cocktails_embedding_agent.domain.models.cocktail_chunking_model import (
    CocktailChunkingModel,
    CocktailDescriptionChunk,
)
from cocktails_embedding_agent.infrastructure.clients.aisearch_api import aisearch_models
from cocktails_embedding_agent.infrastructure.clients.cocktails_api.cocktails_models import (
    CocktailIngredientMatchSearchModel,
    CocktailModel,
    CocktailRatingModel,
    CocktailReportsModel,
    CocktailSearchModel,
)


@pytest.mark.parametrize(
    "model",
    [CocktailModel, CocktailSearchModel, CocktailIngredientMatchSearchModel, CocktailReportsModel],
)
def test_glassware_accepts_unrestricted_strings(model):
    glassware = ["cocktailGlass", "Cocktail Glass", "Custom ceramic cup"]
    adapter = TypeAdapter(model.model_fields["glassware"].annotation)

    assert adapter.validate_json(adapter.dump_json(glassware)) == glassware


@pytest.mark.parametrize(
    "model",
    [
        aisearch_models.CocktailEmbeddingModel,
        aisearch_models.CocktailSearchModel,
        aisearch_models.CocktailIngredientMatchSearchModel,
    ],
)
def test_aisearch_client_glassware_accepts_unrestricted_strings(model):
    glassware = ["cocktailGlass", "Cocktail Glass", "Custom ceramic cup"]
    adapter = TypeAdapter(model.model_fields["glassware"].annotation)

    assert adapter.validate_json(adapter.dump_json(glassware)) == glassware


def test_handler_preserves_glassware_when_sending_to_aisearch():
    glassware = ["Cocktail Glass", "doubleRocks", "Custom ceramic cup"]
    settings = SimpleNamespace(bootstrap_servers="localhost:9092")
    options = SimpleNamespace(consumer_topic_name="embedding")
    client = SimpleNamespace(create_embeddings=AsyncMock())
    handler = ProcessEmbeddingEventCommandHandler(settings, options, settings, client)
    cocktail = CocktailModel.model_construct(
        id="test",
        locale="en",
        title="Test",
        descriptiveTitle="Test Cocktail",
        serves=1,
        prepTimeMinutes=5,
        isIba=False,
        ingredients=[],
        glassware=glassware,
        rating=CocktailRatingModel.model_construct(rating=4.5),
        images=[],
        keywords=None,
    )
    command = ProcessEmbeddingEventCommand(
        CocktailChunkingModel(cocktail_model=cocktail, chunks=[CocktailDescriptionChunk("desc", "test")])
    )

    assert asyncio.run(handler.handle(command)) is True
    request = client.create_embeddings.await_args.args[0]
    assert request.model_dump(mode="json")["cocktailEmbeddingModel"]["glassware"] == glassware
