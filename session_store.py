from copy import deepcopy
from threading import Lock
from typing import Any
from uuid import uuid4


Message = dict[str, Any]


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, list[Message]] = {}
        self._lock = Lock()

    def create_session(self, session_id: str | None = None) -> str:
        resolved_session_id = session_id or uuid4().hex
        with self._lock:
            self._sessions.setdefault(resolved_session_id, [])
        return resolved_session_id

    def get_messages(self, session_id: str) -> list[Message]:
        with self._lock:
            return deepcopy(self._sessions.setdefault(session_id, []))

    def save_messages(self, session_id: str, messages: list[Message]) -> None:
        with self._lock:
            self._sessions[session_id] = deepcopy(messages)

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions[session_id] = []

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def list_sessions(self) -> list[str]:
        with self._lock:
            return sorted(self._sessions.keys())
