"""HashEmbedder — deterministic, dependency-free stub embedder (dev/test)."""

from __future__ import annotations

import hashlib
import math
import struct


class HashEmbedder:
    """Generates a fixed-dim float vector via hashing.

    Deterministic: same text → same vector. Useful in tests and development
    before a real model (sentence-transformers, Ollama, …) is wired in.
    """

    def __init__(self, dim: int = 64) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        self._dim = dim
        self._model_name = f"hash-stub-{dim}"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dim(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        repeats = (self._dim * 4 + len(digest) - 1) // len(digest)
        raw = (digest * repeats)[: self._dim * 4]
        ints = struct.unpack(f"{self._dim}I", raw)
        floats = [(value / 0xFFFFFFFF) * 2.0 - 1.0 for value in ints]
        norm = math.sqrt(sum(float_value * float_value for float_value in floats)) or 1.0
        return [float_value / norm for float_value in floats]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]
