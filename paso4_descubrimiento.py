"""Paso 4: el agente empieza solo con un buscador y habilita las tools que encuentra."""

from pydantic_ai import RunContext

from base import CATALOG, Chat


def discover_tools(ctx: RunContext[Chat], keyword: str) -> dict[str, str]:
    """Busca herramientas por nombre o descripción y las habilita en la siguiente llamada."""
    found = {}
    for name, description in CATALOG.items():
        if keyword.lower() in f"{name} {description}".lower():
            found[name] = description
    # available_tools (chat_agent.py) envía estas tools al modelo desde la siguiente llamada.
    ctx.deps.loaded_tools.update(found)
    return found
