from dataclasses import dataclass
from typing import Optional

from cocktails_chunking_agent.infrastructure.clients.cocktails_api.cocktail_api import CocktailModel


@dataclass
class CocktailExtractionModel:
    extraction_text: str
    cocktail_model: Optional[CocktailModel] = None

    def as_serializable_json(self) -> bytes:
        from pydantic import TypeAdapter

        serializable_dict = {
            "cocktail_model": self.cocktail_model.model_dump() if self.cocktail_model is not None else None,
            "extraction_text": self.extraction_text,
        }
        return TypeAdapter(dict).dump_json(serializable_dict)
