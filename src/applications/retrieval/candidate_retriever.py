from dataclasses import dataclass

from src.foundation.embeddings.embedding_provider import EmbeddingProvider
from src.foundation.vector_store.vector_store import VectorStore


@dataclass
class CandidateResult:
    candidate_id: str
    first_name: str
    last_name: str
    content_preview: str
    score: float


class CandidateRetriever:

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        index_name: str = "candidates_index",
    ) -> None:
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider
        self._index_name = index_name

    def search(self, query: str, top_k: int = 10) -> list[CandidateResult]:
        if not query.strip():
            raise ValueError("Query cannot be empty.")

        query_vector = self._embedding_provider.embed(query)

        results = self._vector_store.search(
            index_name=self._index_name,
            query_vector=query_vector,
            top_k=top_k,
        )

        return [
            CandidateResult(
                candidate_id=result.id,
                first_name=result.metadata.get("first_name", ""),
                last_name=result.metadata.get("last_name", ""),
                content_preview=result.metadata.get("content", "")[:200],
                score=round(result.score, 4),
            )
            for result in results
        ]
