# =========================
# vector_store.py
# =========================

from dataclasses import dataclass
from typing import Any


@dataclass
class VectorRecord:

    id: str
    vector: list[float]
    metadata: dict[str, Any]


@dataclass
class SearchResult:

    id: str
    score: float
    metadata: dict[str, Any]


class VectorStore:

    def create_index(
        self,
        index_name: str,
        schema: dict,
    ):
        raise NotImplementedError


    def insert(
        self,
        index_name: str,
        records: list[VectorRecord],
    ):
        raise NotImplementedError


    def search(
        self,
        index_name: str,
        query_vector: list[float],
        top_k: int,
    ):
        raise NotImplementedError


def build_records(
    rows: list[dict],
    id_field: str,
    embedding_field: str = "embedding",
):

    records = []

    for row in rows:

        records.append(
            VectorRecord(
                id=str(
                    row[id_field]
                ),

                vector=row[
                    embedding_field
                ],

                # KEEP ORIGINAL PAYLOAD 100%
                metadata=dict(
                    row
                ),
            )
        )

    return records