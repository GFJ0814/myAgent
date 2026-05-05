from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent_service import AgentService


app = FastAPI(title="MyAgent API")
_service: AgentService | None = None

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateSessionResponse(BaseModel):
    session_id: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str


class ClearSessionResponse(BaseModel):
    session_id: str
    cleared: bool


class MessagesResponse(BaseModel):
    session_id: str
    messages: list[dict[str, Any]]


def get_service() -> AgentService:
    global _service
    if _service is None:
        _service = AgentService()
    return _service


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sessions", response_model=CreateSessionResponse)
def create_session() -> CreateSessionResponse:
    try:
        session_id = get_service().create_session()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return CreateSessionResponse(session_id=session_id)


@app.get("/sessions")
def list_sessions() -> dict[str, list[str]]:
    try:
        sessions = get_service().list_sessions()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"sessions": sessions}


@app.get("/sessions/{session_id}/messages", response_model=MessagesResponse)
def get_session_messages(session_id: str) -> MessagesResponse:
    try:
        messages = get_service().get_history(session_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return MessagesResponse(session_id=session_id, messages=messages)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        reply = get_service().chat(req.session_id, req.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"chat failed: {exc}") from exc
    return ChatResponse(session_id=req.session_id, reply=reply)


@app.post("/sessions/{session_id}/clear", response_model=ClearSessionResponse)
def clear_session(session_id: str) -> ClearSessionResponse:
    try:
        get_service().clear_session(session_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ClearSessionResponse(session_id=session_id, cleared=True)


@app.get("/skills")
def list_skills() -> dict[str, list[dict[str, str]]]:
    try:
        skills = get_service().list_skills()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "skills": [
            {
                "name": name,
                "description": entry["description"],
                "path": entry["path"],
            }
            for name, entry in sorted(skills.items())
        ]
    }


@app.get("/")
def index() -> FileResponse:
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="frontend not built")
    return FileResponse(index_file)


if FRONTEND_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR)),
        name="frontend-static",
    )
