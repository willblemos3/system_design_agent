from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from src.applications.system_design.documents import list_diagrams
from src.applications.system_design.exercise import Exercise
from src.applications.system_design.report import SessionReport
from src.runtime.agent_runtime import AgentRuntime


# Sent as the first user turn so the PM opens the meeting and presents the challenge.
_KICKOFF = (
    "[Session start: the student has just joined and has not seen the brief. "
    "Give your opening message as described in your objective.]"
)


class PMSession:
    """
    Conversational session with the PM persona for one system design exercise.

    Runtime-agnostic: receives any AgentRuntime already configured with the PM instruction.
    - ask()/stream(): conversation with the PM (no message = opening).
    - submit_solution() / answer_tradeoff(): recorded as-is, never sent to the LLM for debate.
    - report(): problem + proposed solution + trade-off answers.
    """

    def __init__(self, runtime: AgentRuntime, exercise: Exercise, pm_name: str) -> None:
        self._runtime = runtime
        self._exercise = exercise
        self._pm_name = pm_name
        self._start()

    def _start(self) -> None:
        self._solution: str | None = None
        self._solution_source: Path | None = None
        self._tradeoff_answers: dict[int, str] = {}
        self._started_at = datetime.now()

    @property
    def exercise(self) -> Exercise:
        return self._exercise

    @property
    def pm_name(self) -> str:
        return self._pm_name

    @property
    def solution(self) -> str | None:
        return self._solution

    @property
    def tradeoff_answers(self) -> dict[int, str]:
        return dict(self._tradeoff_answers)

    def unanswered_tradeoffs(self) -> list[int]:
        return [i for i in range(len(self._exercise.tradeoffs)) if i not in self._tradeoff_answers]

    def has_progress(self) -> bool:
        return self._solution is not None or bool(self._tradeoff_answers)

    async def ask(self, message: str | None = None) -> str:
        return await self._runtime.run(message or _KICKOFF, tools=[])

    async def stream(self, message: str | None = None) -> AsyncIterator[str]:
        async for chunk in self._runtime.stream(message or _KICKOFF, tools=[]):
            yield chunk

    def submit_solution(self, text: str, source: Path | None = None) -> None:
        """source: the file in results/ the solution was loaded from, if any."""
        if not text.strip():
            raise ValueError("Solution cannot be empty.")
        self._solution = text.strip()
        self._solution_source = source

    def answer_tradeoff(self, index: int, text: str) -> None:
        if not 0 <= index < len(self._exercise.tradeoffs):
            raise IndexError(f"Trade-off question {index} does not exist.")
        if not text.strip():
            raise ValueError("Answer cannot be empty.")
        self._tradeoff_answers[index] = text.strip()

    def report(self) -> SessionReport:
        return SessionReport(
            exercise=self._exercise,
            solution=self._solution,
            solution_source=self._solution_source,
            tradeoff_answers=dict(self._tradeoff_answers),
            diagrams=list_diagrams(),
            started_at=self._started_at,
            finished_at=datetime.now(),
        )

    def reset(self) -> None:
        self._runtime.reset()
        self._start()
