import inspect
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from src.foundation.memory.memory_provider import MemoryProvider, MemoryRecord
from src.runtime.agent_runtime import AgentRuntime
from src.tools.tool import Tool, ToolSchema


_TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}

_APP_NAME = "genai_platform"
_USER_ID = "user"


def _build_tool_fn(tool: Tool) -> callable:
    """
    Wraps a Tool into a plain Python callable that ADK can introspect.

    Sets __signature__ so ADK sees typed parameters (not **kwargs),
    which it uses to generate the tool schema sent to the LLM.
    """
    schema: ToolSchema = tool.schema()

    params = [
        inspect.Parameter(
            name=p.name,
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=inspect.Parameter.empty if p.required else None,
            annotation=_TYPE_MAP.get(p.type, str),
        )
        for p in schema.parameters
    ]

    def wrapper(**kwargs):
        result = tool.execute(**kwargs)
        if result.error:
            return {"error": result.error}
        return result.content

    wrapper.__name__ = schema.name
    wrapper.__doc__ = schema.description
    wrapper.__signature__ = inspect.Signature(
        parameters=params,
        return_annotation=dict,
    )

    return wrapper


class ADKRuntime(AgentRuntime):

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        instruction: str = "",
        memory_provider: MemoryProvider | None = None,
        user_id: str = "default_user",
        session_id: str | None = None,
    ) -> None:
        self._model = model
        self._instruction = instruction
        self._memory = memory_provider
        self._user_id = user_id
        self._session_id = session_id or str(uuid.uuid4())

    def _build_runner(self, tools: list[Tool]) -> tuple[Runner, InMemorySessionService]:
        agent = LlmAgent(
            model=self._model,
            name="agent",
            instruction=self._instruction,
            tools=[_build_tool_fn(t) for t in tools],
        )
        session_service = InMemorySessionService()
        runner = Runner(
            agent=agent,
            app_name=_APP_NAME,
            session_service=session_service,
        )
        return runner, session_service

    def _save_turn(self, user_text: str, agent_text: str) -> None:
        if not self._memory or not agent_text:
            return
        now = datetime.now(timezone.utc).isoformat()
        self._memory.save(MemoryRecord(
            id=str(uuid.uuid4()),
            user_id=self._user_id,
            session_id=self._session_id,
            role="user",
            text=user_text,
            timestamp=now,
        ))
        self._memory.save(MemoryRecord(
            id=str(uuid.uuid4()),
            user_id=self._user_id,
            session_id=self._session_id,
            role="agent",
            text=agent_text,
            timestamp=now,
        ))

    async def run(self, input: str, tools: list[Tool]) -> str:
        runner, session_service = self._build_runner(tools)

        session = await session_service.create_session(
            app_name=_APP_NAME,
            user_id=_USER_ID,
        )

        parts = []
        async for event in runner.run_async(
            user_id=_USER_ID,
            session_id=session.id,
            new_message=Content(parts=[Part(text=input)]),
        ):
            if event.is_final_response() and event.content:
                parts.extend(
                    part.text
                    for part in event.content.parts
                    if part.text
                )

        response = "".join(parts)
        self._save_turn(input, response)
        return response

    async def stream(self, input: str, tools: list[Tool]) -> AsyncIterator[str]:
        runner, session_service = self._build_runner(tools)

        session = await session_service.create_session(
            app_name=_APP_NAME,
            user_id=_USER_ID,
        )

        chunks: list[str] = []
        try:
            async for event in runner.run_async(
                user_id=_USER_ID,
                session_id=session.id,
                new_message=Content(parts=[Part(text=input)]),
            ):
                if event.content:
                    for part in event.content.parts:
                        if part.text:
                            chunks.append(part.text)
                            yield part.text
        finally:
            self._save_turn(input, "".join(chunks))
