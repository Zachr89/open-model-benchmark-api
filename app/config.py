from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/benchmark_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # OpenRouter
    OPENROUTER_API_KEY: str
    
    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    
    # App
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # Rate limits
    FREE_TIER_MONTHLY_LIMIT: int = 10
    PRO_TIER_MONTHLY_LIMIT: int = 500
    TEAM_TIER_MONTHLY_LIMIT: int = 2500

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
