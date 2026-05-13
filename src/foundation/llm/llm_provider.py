from abc import ABC, abstractmethod
from typing import Iterator, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str: ...

    @abstractmethod
    def structured_generate(self, prompt: str, schema: type[T], **kwargs) -> T: ...

    @abstractmethod
    def stream(self, prompt: str, **kwargs) -> Iterator[str]: ...
