"""Customer Success Platform Configuration."""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Verdis Customer Success Platform"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 3400
    WORKERS: int = 4
    
    # Database (shared with EvolvixOS)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://evolvixos:EvolvixOS2026@localhost:5432/evolvixos")
    
    # Redis (shared)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/2")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 2000
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "evolvixos_cs_secret_2026")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 30
    RATE_LIMIT_BURST: int = 10
    
    # Knowledge Base
    KB_DOCS_PATH: str = "/opt/evolvixos-repo/aegisos/backend/docs"
    KB_WHITEPAPER_PATH: str = "/opt/evolvixos-repo/docs/whitepaper.md"
    
    # EvolvixOS API
    EVOLVIXOS_API_URL: str = "http://localhost:3200/api/v1"
    EVOLVIXOS_API_KEY: str = os.getenv("EVOLVIXOS_API_KEY", "")
    
    # Verdis Blockchain
    VERDIS_RPC_URL: str = "http://localhost:3200/blockchain/rpc"
    VERDIS_API_URL: str = "http://localhost:3200/blockchain/api"
    
    # Integrations
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    DISCORD_WEBHOOK: str = os.getenv("DISCORD_WEBHOOK", "")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    SLACK_WEBHOOK: str = os.getenv("SLACK_WEBHOOK", "")
    
    # Monitoring
    GRAFANA_URL: str = "http://localhost:3000"
    PROMETHEUS_URL: str = "http://localhost:9090"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
