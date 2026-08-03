"""Mock AI provider — deterministic, no external calls, no API cost.

The embedder is a hashed bag-of-words vector: each word is hashed into one of
EMBEDDING_DIM buckets and counted, then L2-normalized. That gives real (if
crude) "shared keywords -> higher cosine similarity" retrieval behavior,
unlike a purely random vector — mock mode is a genuinely useful stand-in for
dev/test, not just a placeholder that returns fixed output regardless of input.

The generator never invents content: it returns the top-matching chunk's own
text, clearly labeled as mock output. Same no-hallucination principle as the
seeded /similar precedent data — this is legal-aid software, so a stand-in
mode must not fabricate anything that looks like a real answer.
"""
import hashlib
import math
import re

from app.models.document_chunk import EMBEDDING_DIM

_WORD_RE = re.compile(r"[a-z0-9]+")


def mock_embed(text: str) -> list[float]:
    vec = [0.0] * EMBEDDING_DIM
    for word in _WORD_RE.findall(text.lower()):
        bucket = int(hashlib.sha256(word.encode()).hexdigest(), 16) % EMBEDDING_DIM
        vec[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def mock_generate(question: str, chunks: list[dict]) -> dict:
    if not chunks:
        return {
            "answer": "Mock AI mode: no matching content was found in this case's documents.",
            "provider": "mock",
        }
    top = chunks[0]
    snippet = top["content"][:600].strip()
    return {
        "answer": (
            f'[Mock AI mode — no live model call] Based on "{top["document_title"]}", '
            f"the most relevant excerpt found is:\n\n{snippet}"
        ),
        "provider": "mock",
    }
