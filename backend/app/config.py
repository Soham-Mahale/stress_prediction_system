from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017/"
    db_name: str = "stress_management_system"

    gemini_api_key: str | None = None
    huggingfacehub_api_token: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
