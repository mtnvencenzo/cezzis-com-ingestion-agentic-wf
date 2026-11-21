import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from cocktails_embedding_agent.domain.config.aisearch_api_options import AISearchApiOptions
from cocktails_embedding_agent.infrastructure.clients.aisearch_api.aisearch_client import AISearchClient
from cocktails_embedding_agent.infrastructure.clients.aisearch_api.aisearch_models import CocktailEmbeddingRq


def _embedding_rq(locale: str | None) -> Mock:
    embedding_rq = Mock(spec=CocktailEmbeddingRq)
    embedding_rq.locale = locale
    embedding_rq.model_dump_json.return_value = "{}"
    return embedding_rq


def _client_with_response(status_code: int):
    response = Mock(status_code=status_code, text="body")
    http_client = AsyncMock()
    http_client.put = AsyncMock(return_value=response)
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = http_client
    context_manager.__aexit__.return_value = None

    token_provider = Mock()
    token_provider.get_access_token = AsyncMock(return_value="token")
    client = AISearchClient(
        AISearchApiOptions(base_url="https://aisearch.example.com", api_key="key", timeout_seconds=5),
        token_provider,
    )
    return client, http_client, context_manager


class TestAISearchClient:
    def test_create_embeddings_sends_the_locale_as_accept_language(self) -> None:
        client, http_client, context_manager = _client_with_response(204)

        with patch("httpx.AsyncClient", return_value=context_manager):
            assert asyncio.run(client.create_embeddings(_embedding_rq("de"))) is True

        headers = http_client.put.await_args.kwargs["headers"]
        assert headers["Accept-Language"] == "de"

    def test_create_embeddings_omits_accept_language_without_a_locale(self) -> None:
        client, http_client, context_manager = _client_with_response(204)

        with patch("httpx.AsyncClient", return_value=context_manager):
            asyncio.run(client.create_embeddings(_embedding_rq(None)))

        assert "Accept-Language" not in http_client.put.await_args.kwargs["headers"]

    def test_create_embeddings_raises_for_an_unsupported_locale(self) -> None:
        client, _, context_manager = _client_with_response(400)

        with patch("httpx.AsyncClient", return_value=context_manager):
            with pytest.raises(ValueError, match="locale may not be supported"):
                asyncio.run(client.create_embeddings(_embedding_rq("xx")))
