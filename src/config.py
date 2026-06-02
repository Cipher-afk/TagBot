from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    BOT_TOKEN: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    DATABASE_URL: str
    PAYSTACK_SECRET_KEY: str
    EMAIL: str
    DOMAIN_URL: str
    model_config = SettingsConfigDict(env_file=".env")


settings = Config()
