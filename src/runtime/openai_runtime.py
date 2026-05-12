import json
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator

from openai import AsyncOpenAI
from openai import APIError as OpenAIAPIError

from src.foundation.memory.memory_provider import MemoryProvider, MemoryRecord
from src.runtime.agent_runtime import AgentRuntime
from src.tools.tool import Tool, ToolSchema
from src.shared.config import get_api_key
from src.shared.exceptions import ProviderError


def _print_tool_call(name: str, args: dict) -> None:
    print(f"\n[tool call → {name}({args})]", flush=True)


def _build_openai_tool(tool: Tool) -> dict:
    schema: ToolSchema = tool.schema()
    return {
        "type": "function",
        "function": {
            "name": schema.name,
            "description": schema.description,
            "parameters": {
                "type": "object",
                "properties": {
                    p.name: {"type": p.type, "description": p.description}
                    for p in schema.parameters
                },
                "required": [p.name for p in schema.parameters if p.required],
            },
        },
    }


class OpenAIRuntime(AgentRuntime):

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        instruction: str = "",
        memory_provider: MemoryProvider | None = None,
        user_id: str = "default_user",
        session_id: str | None = None,
        verbose: bool = True,
    ) -> None:
        self._model = model
        self._instruction = instruction
        self._memory = memory_provider
        self._user_id = user_id
        self._session_id = session_id or str(uuid.uuid4())
        self._verbose = verbose
        self._client = AsyncOpenAI(api_key=get_api_key("openai"))

    def _base_messages(self, input: str) -> list[dict]:
        messages = []
        if self._instruction:
            messages.append({"role": "system", "content": self._instruction})
        messages.append({"role": "user", "content": input})
        return messages

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
        messages = self._base_messages(input)
        openai_tools = [_build_openai_tool(t) for t in tools]
        tool_map = {t.schema().name: t for t in tools}

        try:
            while True:
                kwargs: dict = {"model": self._model, "messages": messages}
                if openai_tools:
                    kwargs["tools"] = openai_tools
                    kwargs["tool_choice"] = "auto"

                response = await self._client.chat.completions.create(**kwargs)
                msg = response.choices[0].message

                if not msg.tool_calls:
                    result = msg.content or ""
                    self._save_turn(input, result)
                    return result

                messages.append(msg)
                for tc in msg.tool_calls:
                    tool = tool_map.get(tc.function.name)
                    if tool:
                        kwargs_tool = json.loads(tc.function.arguments)
                        if self._verbose:
                            _print_tool_call(tc.function.name, kwargs_tool)
                        tool_result = tool.execute(**kwargs_tool)
                        content = tool_result.content if not tool_result.error else {"error": tool_result.error}
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(content),
                        })

        except OpenAIAPIError as e:
            raise ProviderError(f"OpenAI run failed: {e}") from e

    async def stream(self, input: str, tools: list[Tool]) -> AsyncIterator[str]:
        messages = self._base_messages(input)
        openai_tools = [_build_openai_tool(t) for t in tools]
        tool_map = {t.schema().name: t for t in tools}
        chunks_all: list[str] = []

        try:
            while True:
                kwargs: dict = {"model": self._model, "messages": messages, "stream": True}
                if openai_tools:
                    kwargs["tools"] = openai_tools
                    kwargs["tool_choice"] = "auto"

                tool_calls_buffer: dict[int, dict] = {}
                full_content = ""

                response = await self._client.chat.completions.create(**kwargs)
                async for chunk in response:
                    delta = chunk.choices[0].delta

                    if delta.content:
                        full_content += delta.content
                        chunks_all.append(delta.content)
                        yield delta.content

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {"id": "", "name": "", "arguments": ""}
                            if tc.id:
                                tool_calls_buffer[idx]["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls_buffer[idx]["name"] = tc.function.name
                                if tc.function.arguments:
                                    tool_calls_buffer[idx]["arguments"] += tc.function.arguments

                if not tool_calls_buffer:
                    break

                messages.append({
                    "role": "assistant",
                    "content": full_content or None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {"name": tc["name"], "arguments": tc["arguments"]},
                        }
                        for tc in tool_calls_buffer.values()
                    ],
                })

                for tc in tool_calls_buffer.values():
                    tool = tool_map.get(tc["name"])
                    if tool:
                        kwargs_tool = json.loads(tc["arguments"])
                        if self._verbose:
                            _print_tool_call(tc["name"], kwargs_tool)
                        tool_result = tool.execute(**kwargs_tool)
                        content = tool_result.content if not tool_result.error else {"error": tool_result.error}
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": json.dumps(content),
                        })

        except OpenAIAPIError as e:
            raise ProviderError(f"OpenAI stream failed: {e}") from e
        finally:
            self._save_turn(input, "".join(chunks_all))
