# =========================
# faiss_store.py
# =========================

import faiss
import numpy as np

from src.foundation.vector_store.vector_store import (
    VectorStore,
    SearchResult,
)


class FAISSVectorStore(VectorStore):

    def __init__(self):

        self.indices = {}

        self.metadata = {}

        self.id_maps = {}


    def create_index(
        self,
        index_name: str,
        schema: dict,
    ):

        vector_dim = None

        for field in schema["fields"]:

            if field["type"] == "vector":

                vector_dim = field["dim"]

                break


        if vector_dim is None:
            raise ValueError(
                "Vector field not found."
            )


        # cosine similarity
        index = faiss.IndexFlatIP(
            vector_dim
        )


        self.indices[
            index_name
        ] = index

        self.metadata[
            index_name
        ] = {}

        self.id_maps[
            index_name
        ] = []


    def insert(
        self,
        index_name: str,
        records,
    ):

        vectors = []


        for record in records:

            vector = np.array(
                record.vector,
                dtype=np.float32,
            )


            # cosine
            faiss.normalize_L2(
                vector.reshape(
                    1,
                    -1,
                )
            )


            vectors.append(
                vector
            )


            self.metadata[
                index_name
            ][record.id] = (
                record.metadata
            )


            self.id_maps[
                index_name
            ].append(
                record.id
            )


        vectors = np.array(
            vectors,
            dtype=np.float32,
        )


        self.indices[
            index_name
        ].add(
            vectors
        )


    def search(
        self,
        index_name: str,
        query_vector,
        top_k: int,
    ):

        query = np.array(
            query_vector,
            dtype=np.float32,
        ).reshape(
            1,
            -1,
        )


        faiss.normalize_L2(
            query
        )


        scores, indices = (
            self.indices[
                index_name
            ].search(
                query,
                top_k,
            )
        )


        results = []


        for score, idx in zip(
            scores[0],
            indices[0],
        ):

            if idx == -1:
                continue


            record_id = (
                self.id_maps[
                    index_name
                ][idx]
            )


            metadata = (
                self.metadata[
                    index_name
                ][record_id]
            )


            results.append(
                SearchResult(
                    id=record_id,

                    score=float(
                        score
                    ),

                    metadata=metadata,
                )
            )


        return results