from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MemoryRecord:
    id: str
    user_id: str
    session_id: str
    role: str  # "user" | "agent"
    text: str
    timestamp: str  # ISO 8601


class MemoryProvider(ABC):

    @abstractmethod
    def save(self, record: MemoryRecord) -> None: ...

    @abstractmethod
    def search(
        self,
        query: str,
        user_id: str,
        top_k: int = 10,
        session_id: str | None = None,
        sort_by_time: bool = False,
    ) -> list[MemoryRecord]: ...

    @abstractmethod
    def get_session(
        self,
        session_id: str,
        user_id: str,
    ) -> list[MemoryRecord]: ...
