from abc import ABC, abstractmethod
from typing import Any, Iterator


class LLMProvider(ABC):

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str: ...

    @abstractmethod
    def structured_generate(self, prompt: str, schema: type, **kwargs) -> Any: ...

    @abstractmethod
    def stream(self, prompt: str, **kwargs) -> Iterator[str]: ...
