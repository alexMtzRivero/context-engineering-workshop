"""Servidor local: un chat por pestaña, historial en memoria y archivos en disco."""

import asyncio
import json
from dataclasses import dataclass, field
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai.exceptions import ContentFilterError, UnexpectedModelBehavior
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from chat_agent import ROOT, Chat, compact, context_usage, history_json, respond

app = FastAPI()


@dataclass
class Session:
    chat: Chat
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


sessions: dict[str, Session] = {}


# Cinco clientes casi iguales, unos 205 mil tokens.
DATASET = "datasets/conversacion-muy-larga.json"


class Start(BaseModel):
    """Los toggles de la página al abrir un chat."""

    model_config = ConfigDict(extra="forbid")
    disk: bool = False
    all_tools: bool = False
    compaction: bool = False
    on_demand: bool = False
    subagent: bool = False
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
    sessions[session_id] = Session(Chat(folder=folder, **body.model_dump(exclude={"dataset"})))
    messages = []
    # La conversación muy larga se convierte a mensajes de Pydantic AI sin llamar al modelo.
    if body.dataset:
        messages = json.loads((ROOT / DATASET).read_text())["messages"]
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
    # El lock evita dos turnos al mismo tiempo sobre el mismo historial.
    async with session.lock:
        try:
            return await respond(session.chat, body.message)
        except NotImplementedError as error:
            # Una función del taller que todavía no escribes: el mensaje dice cuál y en qué archivo.
            raise HTTPException(501, str(error)) from error
        except ContentFilterError as error:
            # Con contextos enormes el proveedor a veces rechaza la respuesta; reintentar suele bastar.
            raise HTTPException(502, "El proveedor rechazó la respuesta con su filtro de contenido. Vuelve a enviar la pregunta.") from error
        except UnexpectedModelBehavior as error:
            # Por ejemplo, el modelo se quedó sin tokens de salida antes de responder.
            raise HTTPException(502, f"El modelo no terminó la respuesta: {error}") from error


@app.post("/sessions/{session_id}/compact")
async def summarize(session_id: str, body: Compaction):
    session = session_for(session_id)
    if not session.chat.compaction:
        raise HTTPException(400, "Enciende el toggle de compactación para usar estos botones.")
    async with session.lock:
        try:
            report = await compact(session.chat, body.with_reference)
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
        except NotImplementedError as error:
            raise HTTPException(501, str(error)) from error
        except ContentFilterError as error:
            raise HTTPException(502, "El proveedor rechazó el resumen con su filtro de contenido. Vuelve a intentarlo.") from error
        except UnexpectedModelBehavior as error:
            raise HTTPException(502, f"El modelo no terminó el resumen: {error}") from error
        return {"compaction": report, "context": history_json(session.chat), "context_usage": context_usage(session.chat)}
