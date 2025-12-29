from injector import inject

from cocktails_embedding_agent.domain.config.aisearch_api_options import AISearchApiOptions
from cocktails_embedding_agent.infrastructure.clients.aisearch_api.aisearch_models import CocktailEmbeddingRq
from cocktails_embedding_agent.infrastructure.clients.aisearch_api.iaisearch_client import IAISearchClient


class AISearchClient(IAISearchClient):
    @inject
    def __init__(self, aisearch_api_options: AISearchApiOptions):
        self.aisearch_api_options = aisearch_api_options

    async def create_embeddings(self, embedding_rq: CocktailEmbeddingRq) -> bool:
        """
        Posts to the embeddings endpoint with a CocktailEmbeddingRq model as the body.
        Returns True if successful (204), raises exception otherwise.
        """
        import httpx

        url = f"{self.aisearch_api_options.base_url}/v1/cocktails/embeddings"
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=self.aisearch_api_options.timeout_seconds) as client:
            response = await client.put(url, content=embedding_rq.model_dump_json(), headers=headers)
            if response.status_code == 204:
                return True
            elif response.status_code == 422:
                raise ValueError(f"Unprocessable Entity: {response.text}")
            elif response.status_code == 500:
                raise RuntimeError(f"Server Error: {response.text}")
            else:
                raise Exception(f"Unexpected status code: {response.status_code}, body: {response.text}")
