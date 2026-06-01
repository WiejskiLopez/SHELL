"""hash_embedder.py
HashEmbedder — deterministic, no-dependency stub embedder for tests/dev.

Generates a fixed-dim float vector from the text via hashing — useful as a
default plug while a real model (sentence-transformers / Ollama) is wired in.
"""

from __future__ import annotations

import hashlib
import math
import struct

from shell.memory.rag_index.embedder.embedder import Embedder


class HashEmbedder(Embedder):
    """Deterministic hash-based embedder (dev/test only)."""

    __slots__ = ("_dim", "_model_name")

    def __init__(self, dim: int = 64) -> None:
        self._dim: int = dim
        self._model_name: str = f"hash-stub-{dim}"

    @property
    def model_name_(self) -> str:
        return self._model_name

    @property
    def dim_(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        repeats = (self._dim * 4 + len(digest) - 1) // len(digest)
        raw = (digest * repeats)[: self._dim * 4]
        ints = struct.unpack(f"{self._dim}I", raw)
        floats = [(v / 0xFFFFFFFF) * 2.0 - 1.0 for v in ints]
        norm = math.sqrt(sum(x * x for x in floats)) or 1.0
        return [x / norm for x in floats]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]
