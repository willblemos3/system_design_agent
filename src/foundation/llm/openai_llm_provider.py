from typing import Iterator

from openai import OpenAI
from openai import APIError as OpenAIAPIError

from src.foundation.llm.llm_provider import LLMProvider, T
from src.shared.config import get_api_key
from src.shared.exceptions import ProviderError


_DEFAULT_MODEL = "gpt-4o-mini"


class OpenAILLMProvider(LLMProvider):

    def __init__(self, model: str = _DEFAULT_MODEL) -> None:
        self._model = model
        self._client = OpenAI(api_key=get_api_key("openai"))

    def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except OpenAIAPIError as e:
            raise ProviderError(f"OpenAI generate failed: {e}") from e

    def structured_generate(self, prompt: str, schema: type[T], **kwargs) -> T:
        try:
            system_content = kwargs.get("system_prompt", "Respond with valid JSON only.")
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            return schema.model_validate_json(response.choices[0].message.content)
        except OpenAIAPIError as e:
            raise ProviderError(f"OpenAI structured_generate failed: {e}") from e

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            for chunk in response:
                text = chunk.choices[0].delta.content
                if text:
                    yield text
        except OpenAIAPIError as e:
            raise ProviderError(f"OpenAI stream failed: {e}") from e
