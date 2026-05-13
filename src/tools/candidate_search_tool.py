from dataclasses import asdict

from src.applications.retrieval.candidate_retriever import CandidateRetriever
from src.shared.exceptions import ProviderError
from src.tools.tool import Tool, ToolParameter, ToolResult, ToolSchema


class CandidateSearchTool(Tool):

    def __init__(self, retriever: CandidateRetriever) -> None:
        self._retriever = retriever

    def execute(self, query: str, top_k: int = 10) -> ToolResult:
        try:
            candidates = self._retriever.search(query=query, top_k=top_k)
            return ToolResult(content=[asdict(c) for c in candidates])
        except ValueError as e:
            return ToolResult(content=None, error=str(e))
        except ProviderError as e:
            return ToolResult(content=None, error=str(e))

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="candidate_search",
            description=(
                "Search for candidates matching a natural language query. "
                "Returns a ranked list of candidates with profile information."
            ),
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Natural language description of the ideal candidate.",
                    required=True,
                ),
                ToolParameter(
                    name="top_k",
                    type="integer",
                    description="Maximum number of candidates to return. Defaults to 10.",
                    required=False,
                ),
            ],
        )
