"""
LLM Factory — Dependency Injection for LangChain LLM instances.

All agents call get_llm() instead of instantiating ChatGroq inline.
To swap to a different provider (OpenAI, Anthropic, Ollama), change
only this file — zero changes to any agent code.
"""
from langchain_groq import ChatGroq
from settings import settings


def get_llm(
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 1024,
) -> ChatGroq:
    """
    Factory function for LLM instances.

    Args:
        model: Groq model ID. Defaults to settings.default_model.
        temperature: Sampling temperature (0.0 = deterministic).
        max_tokens: Maximum completion tokens.

    Returns:
        Configured ChatGroq instance ready for .invoke() or .ainvoke().
    """
    return ChatGroq(
        api_key=settings.groq_api_key,
        model_name=model or settings.default_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
