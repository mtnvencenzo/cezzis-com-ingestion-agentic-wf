import json
from typing import Literal

import httpx
from injector import inject

from cocktails_extraction_agent.domain.config.cocktails_api_options import CocktailsApiOptions
from cocktails_extraction_agent.infrastructure.clients.cocktails_api.cocktail_api import (
    CocktailModel,
    CocktailRs,
    ProblemDetails,
)


class CocktailsApiService:
    @inject
    def __init__(self, cocktails_api_options: CocktailsApiOptions) -> None:
        self._cocktails_api_options = cocktails_api_options

    async def get_cocktail(
        self,
        id: str,
        resolve_ingredients: bool = False,
        measurement_system: Literal["imperial", "metric"] = "imperial",
        x_key: str | None = None,
    ) -> CocktailModel:
        if not self._cocktails_api_options.base_url:
            raise ValueError("COCKTAILS_API_BASE_URL environment variable is required to call the cocktails API")

        headers = {"Accept": "application/json; x-api-version=1.0"}
        effective_x_key = x_key if x_key is not None else self._cocktails_api_options.x_key
        if effective_x_key:
            headers["X-Key"] = effective_x_key

        params = {
            "resolveIngredients": resolve_ingredients,
            "measurementSystem": measurement_system,
        }

        async with httpx.AsyncClient(base_url=self._cocktails_api_options.base_url, timeout=30.0) as client:
            response = await client.get(f"/api/v1/cocktails/{id}", params=params, headers=headers)

        if response.is_error:
            detail = self._build_error_detail(response)
            raise httpx.HTTPStatusError(detail, request=response.request, response=response)

        return CocktailRs.model_validate(response.json()).item

    @staticmethod
    def _build_error_detail(response: httpx.Response) -> str:
        try:
            problem_details = ProblemDetails.model_validate(response.json())
        except (json.JSONDecodeError, ValueError, TypeError):
            problem_details = None

        if problem_details and (problem_details.title or problem_details.detail):
            return f"Cocktails API request failed: {problem_details.title or 'Unknown error'}: {problem_details.detail or ''}".rstrip(
                ": "
            )

        return f"Cocktails API request failed with status {response.status_code}"
