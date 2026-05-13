from src.foundation.vector_store.vector_store import VectorStore, VectorRecord, SearchResult, build_records
from src.foundation.vector_store.faiss_store import FAISSVectorStore

__all__ = [
    "VectorStore",
    "VectorRecord",
    "SearchResult",
    "build_records",
    "FAISSVectorStore",
]

try:
    from src.foundation.vector_store.milvus_store import MilvusVectorStore
    __all__.append("MilvusVectorStore")
except ImportError:
    pass
