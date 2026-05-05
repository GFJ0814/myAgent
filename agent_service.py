from typing import Any

from agent_core import agent_loop, build_client, load_capabilities
from session_store import SessionStore


class AgentService:
    def __init__(self, store: SessionStore | None = None) -> None:
        self._store = store or SessionStore()
        self._client = build_client()

    def create_session(self, session_id: str | None = None) -> str:
        return self._store.create_session(session_id)

    def clear_session(self, session_id: str) -> None:
        self._store.clear_session(session_id)

    def delete_session(self, session_id: str) -> None:
        self._store.delete_session(session_id)

    def list_sessions(self) -> list[str]:
        return self._store.list_sessions()

    def get_history(self, session_id: str) -> list[dict[str, Any]]:
        return self._store.get_messages(session_id)

    def list_capabilities(self) -> dict[str, dict[str, Any]]:
        return load_capabilities()

    def list_skills(self) -> dict[str, dict[str, Any]]:
        return {
            name: entry
            for name, entry in load_capabilities().items()
            if entry.get("kind") == "skill"
        }

    def chat(self, session_id: str, user_input: str) -> str:
        resolved_session_id = self._store.create_session(session_id)
        messages = self._store.get_messages(resolved_session_id)
        reply = agent_loop(user_input, messages, self._client)
        self._store.save_messages(resolved_session_id, messages)
        return reply
