"""Plain character-based text chunking for embedding generation."""


def chunk_text(text: str, size: int = 1500, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks of roughly `size` characters.

    Character-based rather than token-based — good enough for chunk-level
    retrieval and avoids adding a tokenizer dependency (tiktoken) for this.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    chunks = []
    start = 0
    step = size - overlap
    while start < len(text):
        chunk = text[start : start + size].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks
