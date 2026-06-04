from __future__ import annotations


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("[RagIndex._chunk_text] chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("[RagIndex._chunk_text] overlap must be in [0, chunk_size)")
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    step = chunk_size - overlap
    for start in range(0, len(text), step):
        chunk = text[start:start + chunk_size]
        if not chunk:
            break
        chunks.append(chunk)
        if start + chunk_size >= len(text):
            break
    return chunks
