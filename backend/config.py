"""
AgenticOS Configuration — Backward-compatibility shim.

All new code should import from `settings` directly.
This module exists so existing env files and references continue to work.
"""
from settings import settings

GROQ_API_KEY = settings.groq_api_key
DEFAULT_MODEL = settings.default_model
AVAILABLE_MODELS = settings.available_models
EMBEDDING_MODEL = settings.embedding_model
CHROMA_PERSIST_DIR = settings.chroma_persist_dir
HOST = settings.host
PORT = settings.port
