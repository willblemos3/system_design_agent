from collections import defaultdict

from src.foundation.embeddings.embedding_provider import EmbeddingProvider
from src.foundation.memory.memory_provider import MemoryProvider, MemoryRecord
from src.foundation.vector_store.schemas import MEMORY_SCHEMA
from src.foundation.vector_store.vector_store import VectorRecord, VectorStore

_INDEX_NAME = "user_conversations"
# FAISS has no native metadata filtering — we over-fetch and filter in Python.
# A multiplier of 20 is safe for POC-scale (< 1 000 records per user).
_SEARCH_MULTIPLIER = 20


class VectorMemoryProvider(MemoryProvider):

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._store = vector_store
        self._embedder = embedding_provider
        # In-memory cache keyed by (user_id, session_id) for get_session().
        # Lives only for the current process — vector store is the source of truth.
        self._session_cache: dict[tuple[str, str], list[MemoryRecord]] = defaultdict(list)
        self._store.create_index(index_name=_INDEX_NAME, schema=MEMORY_SCHEMA)

    def save(self, record: MemoryRecord) -> None:
        vector = self._embedder.embed(record.text)
        vr = VectorRecord(
            id=record.id,
            vector=vector,
            metadata={
                "id": record.id,
                "user_id": record.user_id,
                "session_id": record.session_id,
                "role": record.role,
                "text": record.text,
                "timestamp": record.timestamp,
            },
        )
        self._store.insert(index_name=_INDEX_NAME, records=[vr])
        self._session_cache[(record.user_id, record.session_id)].append(record)

    def search(
        self,
        query: str,
        user_id: str,
        top_k: int = 10,
        session_id: str | None = None,
    ) -> list[MemoryRecord]:
        vector = self._embedder.embed(query)
        raw = self._store.search(
            index_name=_INDEX_NAME,
            query_vector=vector,
            top_k=top_k * _SEARCH_MULTIPLIER,
        )
        results: list[MemoryRecord] = []
        for r in raw:
            m = r.metadata
            if m.get("user_id") != user_id:
                continue
            if session_id and m.get("session_id") != session_id:
                continue
            results.append(_to_record(m))
            if len(results) >= top_k:
                break
        return results

    def get_session(
        self,
        session_id: str,
        user_id: str,
    ) -> list[MemoryRecord]:
        return list(self._session_cache[(user_id, session_id)])


def _to_record(metadata: dict) -> MemoryRecord:
    return MemoryRecord(
        id=metadata["id"],
        user_id=metadata["user_id"],
        session_id=metadata["session_id"],
        role=metadata["role"],
        text=metadata["text"],
        timestamp=metadata["timestamp"],
    )
