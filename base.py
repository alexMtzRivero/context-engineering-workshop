"""Piezas que comparten todos los pasos: el estado del chat, el catálogo de tools y las rutas seguras."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import ModelRetry
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter, ModelRequest, ModelResponse, TextPart, UserPromptPart

from customer_tools import CUSTOMER_CATALOG

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
MODEL = os.getenv("MODEL", "anthropic:claude-haiku-5-5")
# La conversación muy larga, en archivos: 00-introduccion.json y uno por cliente (01 a 05), en ese orden.
CONVERSATION = "datasets/conversacion-muy-larga"


@dataclass
class Chat:
    """Estado de una conversación. Cada tool lo recibe como ctx.deps."""

    folder: Path  # carpeta de trabajo de este chat: workspace/<id>/
    archives: Path | None = None  # historiales compactados; la app los guarda junto al código, en archives/
    # Toggles de la página: qué puede usar el agente. Todos apagados = chat básico.
    disk: bool = False  # Leer y escribir en disco
    all_tools: bool = False  # Todas las tools: las 80 de servicio en cada llamada
    compaction: bool = False  # Compactación
    on_demand: bool = False  # Tools bajo demanda
    subagent: bool = False  # Un agente por cliente
    history: list[ModelMessage] = field(default_factory=list)  # lo que se reenvía al modelo en cada llamada
    pending_compaction: bool | None = None  # compactación pedida por el agente; se aplica al terminar el turno
    loaded_tools: set[str] = field(default_factory=set)  # tools descubiertas con Tools bajo demanda
    events: list[str] = field(default_factory=list)  # bitácora del panel "Tools enviadas al modelo"
    last_input_tokens: int | None = None
    service_requests: list[dict] = field(default_factory=list)  # solicitudes simuladas de las tools de escritura
    subagent_runs: list[dict] = field(default_factory=list)  # sub-agentes que corrieron en este turno
    clients: dict[str, Path] = field(default_factory=dict)  # extra: cliente -> el archivo de su conversación


# Nombre y descripción de cada tool que se puede descubrir con Tools bajo demanda.
CATALOG = {
    "list_files": "Encontrar archivos por una palabra en su ruta.",
    "read_file": "Leer un rango de líneas de un archivo de texto, incluido un historial archivado.",
    "search_file": "Buscar un texto dentro de un archivo y ver solo las líneas que coinciden.",
    "write_file": "Guardar texto en un archivo.",
    "compact_context": "Resumir el historial, con o sin referencia al original en disco.",
    **CUSTOMER_CATALOG,
}


def file_path(chat: Chat, name: str) -> Path:
    """Convierte una ruta relativa en una ruta dentro de la carpeta del chat (o de archives/, si el chat la tiene)."""
    root = chat.folder.resolve()
    parts = Path(name).parts
    # archives/ puede vivir fuera de la carpeta del chat, junto al código, para encontrar fácil los historiales.
    if chat.archives is not None and parts[:1] == ("archives",):
        root, name = chat.archives.resolve(), str(Path(*parts[1:])) if len(parts) > 1 else ""
    path = (root / name).resolve()
    # resolve() quita los "..": si la ruta final sale de la carpeta, se rechaza.
    if path == root or not path.is_relative_to(root):
        # ModelRetry le devuelve el error al modelo para que lo intente de nuevo.
        raise ModelRetry("Usa una ruta relativa dentro de la carpeta de trabajo.")
    return path


def history_json(chat: Chat) -> str:
    """El historial serializado tal como lo guarda Pydantic AI."""
    return ModelMessagesTypeAdapter.dump_json(chat.history, indent=2).decode()


def read_messages(path: Path) -> list[dict]:
    """Los mensajes de un archivo del dataset, como {"role", "content"}."""
    return json.loads(path.read_text())["messages"]


def to_model_messages(messages: list[dict]) -> list[ModelMessage]:
    """Convierte mensajes {"role", "content"} en el historial que entiende Pydantic AI, sin llamar al modelo."""
    history = []
    for message in messages:
        if message["role"] == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=message["content"])]))
        else:
            history.append(ModelResponse(parts=[TextPart(content=message["content"])]))
    return history


def read_conversation(path: Path) -> list[ModelMessage]:
    """Lee un archivo del dataset como historial de Pydantic AI."""
    return to_model_messages(read_messages(path))
