from abc import ABC, abstractmethod
from typing import AsyncIterator

from src.tools.tool import Tool, ToolResult


class AgentRuntime(ABC):

    @abstractmethod
    async def run(self, input: str, tools: list[Tool]) -> str: ...

    @abstractmethod
    async def stream(self, input: str, tools: list[Tool]) -> AsyncIterator[str]: ...

    @abstractmethod
    def reset(self) -> None:
        """Clears the conversation history and starts a new session."""

    def invoke_tool(self, tool: Tool, kwargs: dict) -> ToolResult:
        return tool.execute(**kwargs)

    def handoff(self, target_agent: str, context: dict) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} does not support handoff."
        )
