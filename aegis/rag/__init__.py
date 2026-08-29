"""RAG (Retrieval-Augmented Generation) system for Aegis.

Provides:
- Embedding backends (Voyage AI / mock)
- Vector storage (pgvector / in-memory)
- Retrieval layer
- Chat engine ("Ask Aegis")
- Remediation engine
"""

from aegis.rag.chat import ChatEngine, DemoChatEngine
from aegis.rag.embedder import EmbedderBase, MockEmbedder, VoyageEmbedder
from aegis.rag.remediation import DemoRemediationEngine, RemediationEngine
from aegis.rag.retriever import MockRetriever, Retriever
from aegis.rag.store import InMemoryVectorStore, PgVectorStore, VectorStoreBase


def get_retriever(demo: bool = False):
    if demo:
        return MockRetriever()
    embedder = VoyageEmbedder()
    store = PgVectorStore()
    return Retriever(embedder, store)


def get_chat_engine(demo: bool = False):
    if demo:
        return DemoChatEngine()
    raise ValueError("Production ChatEngine requires anthropic_client — use ChatEngine(retriever, client) directly")


def get_remediation_engine(demo: bool = False):
    if demo:
        return DemoRemediationEngine()
    raise ValueError("Production RemediationEngine requires anthropic_client — use RemediationEngine(retriever, client) directly")


__all__ = [
    "ChatEngine",
    "DemoChatEngine",
    "EmbedderBase",
    "MockEmbedder",
    "VoyageEmbedder",
    "RemediationEngine",
    "DemoRemediationEngine",
    "Retriever",
    "MockRetriever",
    "InMemoryVectorStore",
    "PgVectorStore",
    "VectorStoreBase",
    "get_retriever",
    "get_chat_engine",
    "get_remediation_engine",
]
