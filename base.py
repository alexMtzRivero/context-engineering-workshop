"""Piezas que comparten todos los pasos: el estado del chat, el catálogo de tools y las rutas seguras."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import ModelRetry
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from customer_tools import CUSTOMER_CATALOG

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
MODEL = os.getenv("MODEL", "anthropic:claude-sonnet-4-6")


@dataclass
class Chat:
    """Estado de una conversación. Cada tool lo recibe como ctx.deps."""

    folder: Path  # carpeta de trabajo de este chat: workspace/<id>/
    step: int = 1  # paso elegido en el selector de la página
    history: list[ModelMessage] = field(default_factory=list)  # lo que se reenvía al modelo en cada llamada
    pending_compaction: bool | None = None  # compactación pedida por el agente; se aplica al terminar el turno
    loaded_tools: set[str] = field(default_factory=set)  # tools descubiertas en el paso 4
    events: list[str] = field(default_factory=list)  # bitácora del panel "Tools enviadas al modelo"
    last_input_tokens: int | None = None
    service_requests: list[dict] = field(default_factory=list)  # solicitudes simuladas de las tools de escritura
    subagent_runs: list[dict] = field(default_factory=list)  # sub-agentes que corrieron en este turno


# Nombre y descripción de cada tool que se puede descubrir en el paso 4.
CATALOG = {
    "list_files": "Encontrar archivos por una palabra en su ruta.",
    "read_file": "Leer un archivo de texto, incluido un historial archivado.",
    "write_file": "Guardar texto en un archivo.",
    "compact_context": "Resumir el historial, con o sin referencia al original en disco.",
    **CUSTOMER_CATALOG,
}


def file_path(chat: Chat, name: str) -> Path:
    """Convierte una ruta relativa en una ruta dentro de la carpeta del chat."""
    root = chat.folder.resolve()
    path = (root / name).resolve()
    # resolve() quita los "..": si la ruta final sale de la carpeta, se rechaza.
    if path == root or not path.is_relative_to(root):
        # ModelRetry le devuelve el error al modelo para que lo intente de nuevo.
        raise ModelRetry("Usa una ruta relativa dentro de la carpeta de trabajo.")
    return path


def history_json(chat: Chat) -> str:
    """El historial serializado tal como lo guarda Pydantic AI."""
    return ModelMessagesTypeAdapter.dump_json(chat.history, indent=2).decode()
