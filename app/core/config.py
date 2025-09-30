from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from decimal import Decimal
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "currency-converter"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # Auth / JWT
    JWT_SECRET: str = os.getenv("CURRENCY_API_KEY")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 3
    JWT_COOKIE_NAME: str = "access_token"

    # Currency API
    CURRENCY_API_BASE_URL: str = os.getenv("CURRENCY_API_BASE_URL")
    CURRENCY_API_KEY: str = os.getenv("CURRENCY_API_KEY")
    SUPPORTED_CURRENCIES: List[str] = ["BRL", "USD", "EUR", "JPY"]

    # Caching & fallback
    CACHE_TTL_SECONDS: int = 300
    STALE_IF_ERROR_SECONDS: int = 600  # 10 minutes

    # HTTP client
    HTTP_TIMEOUT_SECONDS: int = 10
    HTTP_RETRIES: int = 3

    # Rate limiting
    RATE_LIMIT_PER_SECOND: int = 300
    RATE_LIMIT_DELAY_SECONDS: int = 10

    # Amount constraints
    MAX_AMOUNT: Decimal = Field(default=Decimal("1e12"))

    API_V1_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
