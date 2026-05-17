from dataclasses import asdict

from src.applications.retrieval.experience_retriever import ExperienceRetriever
from src.shared.exceptions import ProviderError
from src.tools.tool import Tool, ToolParameter, ToolResult, ToolSchema


class ExperienceSearchTool(Tool):

    def __init__(self, retriever: ExperienceRetriever) -> None:
        self._retriever = retriever

    def execute(self, query: str, top_k: int = 10) -> ToolResult:
        try:
            experiences = self._retriever.search(query=query, top_k=top_k)
            return ToolResult(content=[asdict(e) for e in experiences])
        except ValueError as e:
            return ToolResult(content=None, error=str(e))
        except ProviderError as e:
            return ToolResult(content=None, error=str(e))

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="experience_search",
            description=(
                "Search individual work experiences across all candidates. "
                "Use this to find specific roles, skills at a company, or career patterns. "
                "Returns matched experiences with candidate_id to cross-reference with candidate_search."
            ),
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Natural language description of the experience to find (e.g. 'machine learning engineer at a startup').",
                    required=True,
                ),
                ToolParameter(
                    name="top_k",
                    type="integer",
                    description="Maximum number of experiences to return. Defaults to 10.",
                    required=False,
                ),
            ],
        )
