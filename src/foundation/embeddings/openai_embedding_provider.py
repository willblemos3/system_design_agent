from openai import OpenAI
from openai import APIError as OpenAIAPIError

from src.foundation.embeddings.embedding_provider import EmbeddingProvider
from src.shared.config import get_api_key
from src.shared.exceptions import ProviderError


_DEFAULT_MODEL = "text-embedding-3-large"  # 3072-dim — matches gemini-embedding-001


class OpenAIEmbeddingProvider(EmbeddingProvider):

    def __init__(self, model: str = _DEFAULT_MODEL) -> None:
        self._model = model
        self._client = OpenAI(api_key=get_api_key("openai"))

    def embed(self, text: str) -> list[float]:
        try:
            response = self._client.embeddings.create(
                input=text,
                model=self._model,
            )
            return response.data[0].embedding
        except OpenAIAPIError as e:
            raise ProviderError(f"OpenAI embed failed: {e}") from e

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self._client.embeddings.create(
                input=texts,
                model=self._model,
            )
            return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        except OpenAIAPIError as e:
            raise ProviderError(f"OpenAI embed_batch failed: {e}") from e
