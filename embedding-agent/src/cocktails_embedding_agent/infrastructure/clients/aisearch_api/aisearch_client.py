from injector import inject

from cocktails_embedding_agent.domain.config.aisearch_api_options import AISearchApiOptions
from cocktails_embedding_agent.infrastructure.clients.aisearch_api.aisearch_models import CocktailEmbeddingRq
from cocktails_embedding_agent.infrastructure.clients.aisearch_api.iaisearch_client import IAISearchClient
from cocktails_embedding_agent.infrastructure.clients.oauth.oauth_token_provider import IOAuthTokenProvider


class AISearchClient(IAISearchClient):
    @inject
    def __init__(self, aisearch_api_options: AISearchApiOptions, oauth_token_provider: IOAuthTokenProvider):
        self.aisearch_api_options = aisearch_api_options
        self.oauth_token_provider = oauth_token_provider

    async def create_embeddings(self, embedding_rq: CocktailEmbeddingRq) -> bool:
        """
        Posts to the embeddings endpoint with a CocktailEmbeddingRq model as the body.
        Uses OAuth 2.0 Bearer token authentication via OAuth M2M application.
        Returns True if successful (204), raises exception otherwise.
        """
        import httpx

        # Get access token from OAuth
        access_token = await self.oauth_token_provider.get_access_token()

        url = f"{self.aisearch_api_options.base_url}/v1/cocktails/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        async with httpx.AsyncClient(timeout=self.aisearch_api_options.timeout_seconds) as client:
            response = await client.put(url, content=embedding_rq.model_dump_json(), headers=headers)
            if response.status_code == 204:
                return True
            elif response.status_code == 401:
                raise RuntimeError(f"Unauthorized: {response.text}")
            elif response.status_code == 403:
                raise RuntimeError(f"Forbidden - insufficient permissions: {response.text}")
            elif response.status_code == 422:
                raise ValueError(f"Unprocessable Entity: {response.text}")
            elif response.status_code == 500:
                raise RuntimeError(f"Server Error: {response.text}")
            else:
                raise Exception(f"Unexpected status code: {response.status_code}, body: {response.text}")
