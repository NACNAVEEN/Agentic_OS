"""
AgenticOS — Application Settings
Uses Pydantic BaseSettings for type-safe, environment-driven configuration.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM
    groq_api_key: str = ""
    default_model: str = "llama-3.3-70b-versatile"

    # Available models for evaluation / selection
    available_models: dict = {
        "llama-3.3-70b": "llama-3.3-70b-versatile",
        "qwen-qwq-32b": "qwen-qwq-32b",
        "deepseek-r1-70b": "deepseek-r1-distill-llama-70b",
        "gemma2-9b": "gemma2-9b-it",
        "mistral-saba-24b": "mistral-saba-24b",
        "llama-4-scout": "meta-llama/llama-4-scout-17b-16e-instruct",
    }

    # RAG / Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_persist_dir: str = "./chroma_db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
        "http://localhost:3000",
    ]


# Singleton settings instance
settings = Settings()
