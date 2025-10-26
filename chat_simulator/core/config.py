"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # LLM Settings
    LLM_PROVIDER: str = "openai"  # openai, anthropic, ollama
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_API_KEY: str  # Required: Set in .env file
    LLM_BASE_URL: str  # Required: Set in .env file
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 300  # Reduced for concise responses
    
    # Queue Settings
    MAX_QUEUE_SIZE: int = 1000
    MESSAGE_TIMEOUT: int = 30
    
    # Memory Settings
    SHORT_TERM_MEMORY_SIZE: int = 10
    LONG_TERM_MEMORY_SIZE: int = 100
    
    # Simulation Settings
    DEFAULT_SIMULATION_TYPE: str = "chat"  # chat, views
    MAX_PERSONAS: int = 20
    
    # Letta Settings (for Global Agent only)
    LETTA_API_KEY: str = ""  # Set in .env file (get from https://www.letta.com/)
    LETTA_BASE_URL: str = "https://api.letta.com"
    LETTA_ENABLED: bool = False  # Set to True in .env to enable Letta
    LETTA_AGENT_NAME: str = "global-meta-advisor"
    LETTA_MODEL: str = "openai/gpt-4"
    LETTA_EMBEDDING: str = "openai/text-embedding-3-small"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

