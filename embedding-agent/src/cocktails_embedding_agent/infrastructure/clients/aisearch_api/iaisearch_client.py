from abc import ABC, abstractmethod
from typing import Any, Coroutine

from cocktails_embedding_agent.infrastructure.clients.aisearch_api.aisearch_models import CocktailEmbeddingRq


class IAISearchClient(ABC):
    @abstractmethod
    def create_embeddings(self, embedding_rq: CocktailEmbeddingRq) -> Coroutine[Any, Any, bool]:
        """Create embeddings for the given cocktail embedding request.

        Args:
            embedding_rq (CocktailEmbeddingRq): The cocktail embedding request model.

        Returns:
            bool: True if the embeddings were created successfully, False otherwise.

        """
        pass
