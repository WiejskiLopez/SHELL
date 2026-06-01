"""embedder.py
Embedder — abstract interface for text embedding providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Embedder(ABC):
    """Abstract base for embedding providers (sentence-transformers, OpenAI, Ollama)."""

    __slots__ = ()

    @property
    @abstractmethod
    def model_name_(self) -> str:
        ...

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...
