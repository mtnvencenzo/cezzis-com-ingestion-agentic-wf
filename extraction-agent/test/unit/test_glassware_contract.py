import pytest
from pydantic import TypeAdapter

from cocktails_extraction_agent.infrastructure.clients.cocktails_api.cocktail_api import (
    CocktailIngredientMatchSearchModel,
    CocktailModel,
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
