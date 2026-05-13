from src.foundation.memory.memory_provider import MemoryProvider
from src.tools.tool import Tool, ToolParameter, ToolResult, ToolSchema


class SearchMemoryTool(Tool):

    def __init__(
        self,
        memory_provider: MemoryProvider,
        user_id: str,
    ) -> None:
        self._memory = memory_provider
        self._user_id = user_id

    def execute(
        self,
        query: str,
        top_k: int = 5,
        session_id: str | None = None,
        sort_by_time: bool = False,
    ) -> ToolResult:
        try:
            records = self._memory.search(
                query=query,
                user_id=self._user_id,
                top_k=top_k,
                session_id=session_id,
                sort_by_time=sort_by_time,
            )
            content = [
                {
                    "role": r.role,
                    "text": r.text,
                    "session_id": r.session_id,
                    "timestamp": r.timestamp,
                }
                for r in records
            ]
            return ToolResult(content=content)
        except Exception as e:
            return ToolResult(content=[], error=str(e))

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="search_memory",
            description=(
                "Search past conversation history for relevant context. "
                "Use this to recall what the user said or what you answered in previous turns."
            ),
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Natural language query to search memory.",
                    required=True,
                ),
                ToolParameter(
                    name="top_k",
                    type="integer",
                    description="Maximum number of memory records to return. Defaults to 5.",
                    required=False,
                ),
                ToolParameter(
                    name="session_id",
                    type="string",
                    description="Filter results to a specific session. Omit to search all sessions for this user.",
                    required=False,
                ),
                ToolParameter(
                    name="sort_by_time",
                    type="boolean",
                    description="If true, return results in chronological order (oldest first). Use when the user asks about their first/earliest message or wants conversation history in order. Defaults to false (semantic similarity order).",
                    required=False,
                ),
            ],
        )
