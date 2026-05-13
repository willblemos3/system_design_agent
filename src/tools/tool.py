from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolParameter:
    name: str
    type: str  # "string" | "integer" | "number" | "boolean" | "array" | "object"
    description: str
    required: bool = True


@dataclass
class ToolSchema:
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)


@dataclass
class ToolResult:
    content: Any
    error: str | None = None


class Tool(ABC):

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult: ...

    @abstractmethod
    def schema(self) -> ToolSchema: ...
