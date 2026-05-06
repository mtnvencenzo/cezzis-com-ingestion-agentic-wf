import asyncio
from unittest.mock import AsyncMock, Mock, patch

from cocktails_extraction_agent.application.services.cocktails_api_service import CocktailsApiService
from cocktails_extraction_agent.domain.config.cocktails_api_options import CocktailsApiOptions


class TestCocktailsApiService:
    def test_get_cocktail_forwards_all_endpoint_parameters_and_returns_cocktail_model(self) -> None:
        expected_model = Mock()
        response = Mock()
        response.is_error = False
        response.json.return_value = {"item": {"id": "adonis"}}

        client = AsyncMock()
        client.get = AsyncMock(return_value=response)

        client_context_manager = AsyncMock()
        client_context_manager.__aenter__.return_value = client
        client_context_manager.__aexit__.return_value = None

        cocktails_api_options = CocktailsApiOptions(
            base_url="https://cocktails.example.com",
            x_key="configured-key",
        )

        service = CocktailsApiService(cocktails_api_options=cocktails_api_options)

        with (
            patch(
                "cocktails_extraction_agent.application.services.cocktails_api_service.httpx.AsyncClient",
                return_value=client_context_manager,
            ) as async_client,
            patch(
                "cocktails_extraction_agent.application.services.cocktails_api_service.CocktailRs.model_validate",
                return_value=Mock(item=expected_model),
            ) as model_validate,
        ):
            result = asyncio.run(
                service.get_cocktail(
                    id="adonis",
                    resolve_ingredients=True,
                    measurement_system="metric",
                    x_key="override-key",
                )
            )

        assert result is expected_model
        async_client.assert_called_once_with(base_url="https://cocktails.example.com", timeout=30.0)
        client.get.assert_awaited_once_with(
            "/api/v1/cocktails/adonis",
            params={"resolveIngredients": True, "measurementSystem": "metric"},
            headers={"Accept": "application/json; x-api-version=1.0", "X-Key": "override-key"},
        )
        model_validate.assert_called_once_with({"item": {"id": "adonis"}})

    def test_get_cocktail_uses_configured_x_key_when_no_override_is_supplied(self) -> None:
        response = Mock()
        response.is_error = False
        response.json.return_value = {"item": {"id": "adonis"}}

        client = AsyncMock()
        client.get = AsyncMock(return_value=response)

        client_context_manager = AsyncMock()
        client_context_manager.__aenter__.return_value = client
        client_context_manager.__aexit__.return_value = None

        cocktails_api_options = CocktailsApiOptions(
            base_url="https://cocktails.example.com",
            x_key="configured-key",
        )

        service = CocktailsApiService(cocktails_api_options=cocktails_api_options)

        with (
            patch(
                "cocktails_extraction_agent.application.services.cocktails_api_service.httpx.AsyncClient",
                return_value=client_context_manager,
            ),
            patch(
                "cocktails_extraction_agent.application.services.cocktails_api_service.CocktailRs.model_validate",
                return_value=Mock(item=Mock()),
            ),
        ):
            asyncio.run(service.get_cocktail(id="adonis"))

        client.get.assert_awaited_once_with(
            "/api/v1/cocktails/adonis",
            params={"resolveIngredients": False, "measurementSystem": "imperial"},
            headers={"Accept": "application/json; x-api-version=1.0", "X-Key": "configured-key"},
        )
