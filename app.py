"""Servidor local: un chat por pestaña, historial en memoria y archivos en disco."""

import asyncio
import json
import re
import unicodedata
from dataclasses import dataclass, field
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai.exceptions import ContentFilterError, UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelRequest, ModelResponse, TextPart, UserPromptPart

from chat_agent import ROOT, Chat, compact, context_usage, file_path, history_json, respond

app = FastAPI()


@dataclass
class Session:
    chat: Chat
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


sessions: dict[str, Session] = {}


# Cinco clientes casi iguales, unos 205 mil tokens.
DATASET = "datasets/conversacion-muy-larga.json"
# Con contextos enormes el filtro de contenido del proveedor a veces bloquea la respuesta; reintentar suele bastar.
FILTER_RETRIES = 2


async def with_filter_retry(call):
    """Repite la llamada si el filtro la bloquea; a la tercera, el error llega a la página."""
    for attempt in range(FILTER_RETRIES + 1):
        try:
            return await call()
        except ContentFilterError:
            if attempt == FILTER_RETRIES:
                raise
            print(f"Filtro de contenido del proveedor: reintento {attempt + 1} de {FILTER_RETRIES}.", flush=True)


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
    # Los historiales compactados van a archives/, junto al código; lo demás, a la carpeta del chat.
    chat = Chat(folder=folder, archives=ROOT / "archives", **body.model_dump(exclude={"dataset"}))
    sessions[session_id] = Session(chat)
    messages = []
    # La conversación muy larga se convierte a mensajes de Pydantic AI sin llamar al modelo.
    if body.dataset:
        messages = json.loads((ROOT / DATASET).read_text())["messages"]
        if chat.subagent:
            # Extra: cada cliente se queda con su conversación y el principal empieza vacío.
            split_by_client(chat, messages)
            messages = []
        else:
            chat.history = to_history(messages)
    return {
        "session_id": session_id, "folder": str(folder), "messages": messages, "clients": list(chat.clients),
        "context_usage": context_usage(chat),
    }


def to_history(messages: list[dict]) -> list:
    return [
        ModelRequest(parts=[UserPromptPart(content=message["content"])])
        if message["role"] == "user" else ModelResponse(parts=[TextPart(content=message["content"])])
        for message in messages
    ]


def split_by_client(chat: Chat, messages: list[dict]) -> None:
    """Guarda la conversación de cada cliente en clientes/<cliente>.json; cada caso empieza con «Hola, soy...»."""
    starts = [index for index, message in enumerate(messages) if message["content"].startswith("Hola, soy")]
    for start, end in zip(starts, [*starts[1:], len(messages)]):
        name = re.search(r"coordinadora de operaciones de ([^.]+)\.", messages[start]["content"]).group(1)
        slug = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()).strip("-")
        reference = f"clientes/{slug}.json"
        path = file_path(chat, reference)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(ModelMessagesTypeAdapter.dump_json(to_history(messages[start:end]), indent=2))
        chat.clients[name] = reference


@app.post("/sessions/{session_id}/chat")
async def send(session_id: str, body: Message):
    session = session_for(session_id)
    # El lock evita dos turnos al mismo tiempo sobre el mismo historial.
    async with session.lock:
        try:
            return await with_filter_retry(lambda: respond(session.chat, body.message))
        except NotImplementedError as error:
            # Una función del taller que todavía no escribes: el mensaje dice cuál y en qué archivo.
            raise HTTPException(501, str(error)) from error
        except ContentFilterError as error:
            raise HTTPException(502, "El proveedor rechazó la respuesta con su filtro de contenido tres veces seguidas. Vuelve a enviar la pregunta.") from error
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
            report = await with_filter_retry(lambda: compact(session.chat, body.with_reference))
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
        except NotImplementedError as error:
            raise HTTPException(501, str(error)) from error
        except ContentFilterError as error:
            raise HTTPException(502, "El proveedor rechazó el resumen con su filtro de contenido tres veces seguidas. Vuelve a intentarlo.") from error
        except UnexpectedModelBehavior as error:
            raise HTTPException(502, f"El modelo no terminó el resumen: {error}") from error
        return {"compaction": report, "context": history_json(session.chat), "context_usage": context_usage(session.chat)}
