"""RAG (Retrieval-Augmented Generation) system for Aegis.

Provides:
- Embedding backends (Hugging Face free tier / Voyage AI / mock)
- Vector storage (pgvector / in-memory)
- Retrieval layer
- Chat engine ("Ask Aegis")
- Remediation engine
"""

from aegis.rag.chat import ChatEngine, DemoChatEngine
from aegis.rag.embedder import EmbedderBase, HuggingFaceEmbedder, MockEmbedder, VoyageEmbedder
from aegis.rag.remediation import DemoRemediationEngine, RemediationEngine
from aegis.rag.retriever import MockRetriever, Retriever
from aegis.rag.store import InMemoryVectorStore, PgVectorStore, VectorStoreBase


def get_retriever(demo: bool = False):
    if demo:
        return MockRetriever()
    embedder = HuggingFaceEmbedder()
    store = PgVectorStore()
    return Retriever(embedder, store)


def get_chat_engine(demo: bool = False):
    if demo:
        return DemoChatEngine()
    from aegis.llm import LLMClient
    retriever = get_retriever(demo=False)
    client = LLMClient()
    return ChatEngine(retriever, client)


def get_remediation_engine(demo: bool = False):
    if demo:
        return DemoRemediationEngine()
    from aegis.llm import LLMClient
    retriever = get_retriever(demo=False)
    client = LLMClient()
    return RemediationEngine(retriever, client)


__all__ = [
    "ChatEngine",
    "DemoChatEngine",
    "EmbedderBase",
    "HuggingFaceEmbedder",
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
