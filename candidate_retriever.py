# =========================
# candidate_retriever.py
# =========================

import numpy as np

from embedding import embed


class CandidateRetriever:

    def __init__(
        self,
        vector_store,
        index_name: str = "candidates_index",
    ):

        self.vector_store = vector_store
        self.index_name = index_name


    def search(
        self,
        query: str,
        top_k: int = 10,
    ):

        if not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )


        query_vector = embed(
            query
        )


        if isinstance(
            query_vector,
            np.ndarray,
        ):
            query_vector = (
                query_vector.tolist()
            )


        results = (
            self.vector_store.search(
                index_name=self.index_name,

                query_vector=query_vector,

                top_k=top_k,
            )
        )


        formatted_results = []

        for result in results:

            metadata = (
                result.metadata
            )

            formatted_results.append(
                {
                    "candidate_id": result.id,

                    "first_name": metadata.get(
                        "first_name"
                    ),

                    "last_name": metadata.get(
                        "last_name"
                    ),

                    "content": (
                        metadata.get(
                            "content",
                            "",
                        )[:200]
                        + "..."
                    ),

                    "score": round(
                        result.score,
                        4,
                    ),
                }
            )


        return formatted_results