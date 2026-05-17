from src.applications.parsing.resume_parser import ResumeParser
from src.tools.tool import Tool, ToolParameter, ToolResult, ToolSchema


class ParseResumeTool(Tool):

    def __init__(self, resume_parser: ResumeParser) -> None:
        self._parser = resume_parser

    def execute(self, resume_text: str) -> ToolResult:
        try:
            experiences = self._parser.parse(resume_text)
            return ToolResult(content=[e.model_dump() for e in experiences])
        except Exception as e:
            return ToolResult(content=[], error=str(e))

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="parse_resume",
            description=(
                "Extract structured work experience from a raw resume text. "
                "Returns a list of positions with company, job title, dates, and details."
            ),
            parameters=[
                ToolParameter(
                    name="resume_text",
                    type="string",
                    description="The full text content of the resume to parse.",
                    required=True,
                ),
            ],
        )
