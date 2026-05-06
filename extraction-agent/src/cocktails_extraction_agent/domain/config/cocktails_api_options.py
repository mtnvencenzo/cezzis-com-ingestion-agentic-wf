import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CocktailsApiOptions(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{os.environ.get('ENV')}"),
        env_file_encoding="utf-8",
        extra="allow",
        populate_by_name=True,
    )

    base_url: str = Field(default="", validation_alias="COCKTAILS_API_BASE_URL")
    x_key: str = Field(default="", validation_alias="COCKTAILS_API_X_KEY")
