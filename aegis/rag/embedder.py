"""Embedding backends for the Aegis RAG system.

Production: VoyageEmbedder (voyage-3-lite, 1024-dim).
Demo: MockEmbedder (zero-vectors, no external calls).
"""

import logging
import math
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

try:
    import voyageai
    HAS_VOYAGE = True
except ImportError:
    HAS_VOYAGE = False


class EmbedderBase(ABC):

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


class VoyageEmbedder(EmbedderBase):

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "voyage-3-lite",
        dimensions: int = 1024,
    ) -> None:
        if not HAS_VOYAGE:
            raise ImportError(
                "voyageai is not installed. Install with: pip install 'aegis[rag]'"
            )
        key = api_key or os.environ.get("VOYAGE_API_KEY", "")
        if not key:
            raise ValueError("VOYAGE_API_KEY is required for VoyageEmbedder")
        self._client = voyageai.AsyncClient(api_key=key)
        self._model = model
        self._dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        result = await self._client.embed([text], model=self._model)
        return result.embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        batch_size = 128
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            result = await self._client.embed(batch, model=self._model)
            all_embeddings.extend(result.embeddings)
        return all_embeddings


class MockEmbedder(EmbedderBase):

    def __init__(self, dimensions: int = 1024) -> None:
        self._dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        vec = [0.0] * self._dimensions
        if not text:
            return vec
        for i, ch in enumerate(text.encode("utf-8")[:self._dimensions]):
            vec[i] = (ch / 255.0) - 0.5
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]
