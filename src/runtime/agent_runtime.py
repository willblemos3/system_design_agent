from abc import ABC, abstractmethod
from typing import Iterator

from src.tools.tool import Tool, ToolResult


class AgentRuntime(ABC):

    @abstractmethod
    def run(self, input: str, tools: list[Tool]) -> str: ...

    @abstractmethod
    def stream(self, input: str, tools: list[Tool]) -> Iterator[str]: ...

    @abstractmethod
    def invoke_tool(self, tool: Tool, kwargs: dict) -> ToolResult: ...

    @abstractmethod
    def handoff(self, target_agent: str, context: dict): ...
