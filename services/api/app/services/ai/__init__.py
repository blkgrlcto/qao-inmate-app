"""AI service dispatch — mock mode by default, OpenAI when OPENAI_API_KEY is set.

This is the only place callers should import from; nothing outside this
package should reach into .mock or .openai_client directly, so the
mock-vs-real switch stays in exactly one place.
"""
from app.core.config import get_settings
from app.services.ai.mock import mock_embed, mock_generate
from app.services.ai.openai_client import openai_embed_batch, openai_generate


async def embed_texts(texts: list[str]) -> tuple[list[list[float]], str]:
    """Returns (embeddings, provider_used)."""
    settings = get_settings()
    if settings.OPENAI_API_KEY:
        return await openai_embed_batch(texts), "openai"
    return [mock_embed(t) for t in texts], "mock"


async def embed_query(text: str) -> tuple[list[float], str]:
    embeddings, provider = await embed_texts([text])
    return embeddings[0], provider


async def generate_answer(question: str, chunks: list[dict]) -> dict:
    settings = get_settings()
    if settings.OPENAI_API_KEY:
        return await openai_generate(question, chunks)
    return mock_generate(question, chunks)
