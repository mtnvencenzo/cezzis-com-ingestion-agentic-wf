import logging
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OAuthOptions(BaseSettings):
    """
    OAuth 2.0 client credentials flow settings.

    Attributes:
        domain (str): OAuth domain (e.g., 'your-tenant.auth0.com').
        client_id (str): OAuth M2M application client ID.
        client_secret (str): OAuth M2M application client secret.
        audience (str): API identifier/audience for the target API.
        scope (str): Requested scopes (e.g., 'write:embeddings').
    """

    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{os.environ.get('ENV')}", ".env.loc"), env_file_encoding="utf-8", extra="allow"
    )

    domain: str = Field(default="", validation_alias="OAUTH_DOMAIN")
    client_id: str = Field(default="", validation_alias="OAUTH_CLIENT_ID")
    client_secret: str = Field(default="", validation_alias="OAUTH_CLIENT_SECRET")
    audience: str = Field(default="", validation_alias="OAUTH_AUDIENCE")
    scope: str = Field(default="", validation_alias="OAUTH_WRITE_EMBEDDINGS_SCOPE")


_logger: logging.Logger = logging.getLogger("oauth_options")
_oauth_options: OAuthOptions | None = None


def get_oauth_options() -> OAuthOptions:
    """
    Get the singleton instance of OAuthOptions.

    Returns:
        OAuthOptions: The OAuth settings instance.
    """
    global _oauth_options
    if _oauth_options is None:
        _oauth_options = OAuthOptions()

        # Validate required configuration
        if not _oauth_options.domain:
            raise ValueError("OAUTH_DOMAIN environment variable is required")
        if not _oauth_options.client_id:
            raise ValueError("OAUTH_CLIENT_ID environment variable is required")
        if not _oauth_options.client_secret:
            raise ValueError("OAUTH_CLIENT_SECRET environment variable is required")
        if not _oauth_options.audience:
            raise ValueError("OAUTH_AUDIENCE environment variable is required")
        if not _oauth_options.scope:
            raise ValueError("OAUTH_WRITE_EMBEDDINGS_SCOPE environment variable is required")

        _logger.info("OAuth settings loaded successfully.")

    return _oauth_options
