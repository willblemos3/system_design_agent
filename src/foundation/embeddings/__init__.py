from src.foundation.embeddings.embedding_provider import EmbeddingProvider
from src.foundation.embeddings.gemini_embedding_provider import GeminiEmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "GeminiEmbeddingProvider",
]

try:
    from src.foundation.embeddings.openai_embedding_provider import OpenAIEmbeddingProvider
    __all__.append("OpenAIEmbeddingProvider")
except ImportError:
    pass
