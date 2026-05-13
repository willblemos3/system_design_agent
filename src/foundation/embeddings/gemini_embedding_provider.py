from google import genai
from google.genai import errors as genai_errors

from src.foundation.embeddings.embedding_provider import EmbeddingProvider
from src.shared.config import get_api_key
from src.shared.exceptions import ProviderError


_DEFAULT_MODEL = "gemini-embedding-001"


class GeminiEmbeddingProvider(EmbeddingProvider):

    def __init__(self, model: str = _DEFAULT_MODEL) -> None:
        self._model = model
        self._client = genai.Client(api_key=get_api_key("google"))

    def embed(self, text: str) -> list[float]:
        try:
            response = self._client.models.embed_content(
                model=self._model,
                contents=text,
            )
            return response.embeddings[0].values
        except genai_errors.APIError as e:
            raise ProviderError(f"Gemini embed failed: {e}") from e

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self._client.models.embed_content(
                model=self._model,
                contents=texts,
            )
            return [embedding.values for embedding in response.embeddings]
        except genai_errors.APIError as e:
            raise ProviderError(f"Gemini embed_batch failed: {e}") from e
