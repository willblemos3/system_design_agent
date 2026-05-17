from dataclasses import dataclass

from src.foundation.embeddings.embedding_provider import EmbeddingProvider
from src.foundation.vector_store.vector_store import VectorStore


@dataclass
class ExperienceResult:
    experience_id: str
    candidate_id: str
    job_title: str
    company: str
    start_date: str
    end_date: str | None
    details_preview: str
    score: float


class ExperienceRetriever:

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        index_name: str = "experiences_index",
    ) -> None:
        self._vector_store = vector_store
        self._embedding_provider = embedding_provider
        self._index_name = index_name

    def search(self, query: str, top_k: int = 10) -> list[ExperienceResult]:
        if not query.strip():
            raise ValueError("Query cannot be empty.")

        query_vector = self._embedding_provider.embed(query)

        results = self._vector_store.search(
            index_name=self._index_name,
            query_vector=query_vector,
            top_k=top_k,
        )

        return [
            ExperienceResult(
                experience_id=result.id,
                candidate_id=str(result.metadata.get("candidate_id", "")),
                job_title=result.metadata.get("experience", {}).get("job_title", ""),
                company=result.metadata.get("experience", {}).get("company", ""),
                start_date=result.metadata.get("experience", {}).get("start_date", ""),
                end_date=result.metadata.get("experience", {}).get("end_date"),
                details_preview=result.metadata.get("experience", {}).get("details", "")[:200],
                score=round(result.score, 4),
            )
            for result in results
        ]
