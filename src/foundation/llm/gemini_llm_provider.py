from typing import Iterator

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from src.foundation.llm.llm_provider import LLMProvider, T
from src.shared.config import get_api_key
from src.shared.exceptions import ProviderError


_DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiLLMProvider(LLMProvider):

    def __init__(self, model: str = _DEFAULT_MODEL) -> None:
        self._model = model
        self._client = genai.Client(api_key=get_api_key("google"))

    def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
            return response.text
        except genai_errors.APIError as e:
            raise ProviderError(f"Gemini generate failed: {e}") from e

    def structured_generate(self, prompt: str, schema: type[T], **kwargs) -> T:
        try:
            config_kwargs: dict = {
                "response_mime_type": "application/json",
                "response_schema": schema,
            }
            if system_prompt := kwargs.get("system_prompt"):
                config_kwargs["system_instruction"] = system_prompt
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            return schema.model_validate_json(response.text)
        except genai_errors.APIError as e:
            raise ProviderError(f"Gemini structured_generate failed: {e}") from e

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        try:
            for chunk in self._client.models.generate_content_stream(
                model=self._model,
                contents=prompt,
            ):
                if chunk.text:
                    yield chunk.text
        except genai_errors.APIError as e:
            raise ProviderError(f"Gemini stream failed: {e}") from e
