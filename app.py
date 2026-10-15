"""Servidor local: un chat por pestaña, historial en memoria y archivos en disco."""

import asyncio
import json
from dataclasses import dataclass, field
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from chat_agent import ROOT, Chat, compact, context_usage, history_json, respond

app = FastAPI()


@dataclass
class Session:
    chat: Chat
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


sessions: dict[str, Session] = {}


class Start(BaseModel):
    step: int = Field(default=1, ge=1, le=5)
    dataset: bool = False


class Message(BaseModel):
    message: str = Field(min_length=1)


class Compaction(BaseModel):
    with_reference: bool


def session_for(session_id: str) -> Session:
    if session_id not in sessions:
        raise HTTPException(404, "Chat no encontrado. Abre un chat nuevo.")
    return sessions[session_id]


@app.get("/")
def index():
    return FileResponse(ROOT / "index.html")


@app.post("/sessions")
def start(body: Start):
    session_id = uuid4().hex
    folder = ROOT / "workspace" / session_id
    folder.mkdir(parents=True, exist_ok=True)
    sessions[session_id] = Session(Chat(folder=folder, step=body.step))
    messages = []
    if body.dataset:
        messages = json.loads((ROOT / "datasets/conversacion-larga.json").read_text())["messages"]
        sessions[session_id].chat.history = [
            ModelRequest(parts=[UserPromptPart(content=message["content"])])
            if message["role"] == "user" else ModelResponse(parts=[TextPart(content=message["content"])])
            for message in messages
        ]
    return {
        "session_id": session_id, "folder": str(folder),
        "messages": messages, "context_usage": context_usage(sessions[session_id].chat),
    }


@app.post("/sessions/{session_id}/chat")
async def send(session_id: str, body: Message):
    session = session_for(session_id)
    async with session.lock:
        return await respond(session.chat, body.message)


@app.post("/sessions/{session_id}/compact")
async def summarize(session_id: str, body: Compaction):
    session = session_for(session_id)
    if session.chat.step < 3:
        raise HTTPException(400, "La compactación está disponible desde el paso 3.")
    async with session.lock:
        try:
            report = await compact(session.chat, body.with_reference)
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
        return {"compaction": report, "context": history_json(session.chat), "context_usage": context_usage(session.chat)}
