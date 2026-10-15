"""Paso 4: el agente empieza solo con un buscador y habilita las tools que encuentra."""

from pydantic_ai import RunContext

from base import CATALOG, Chat


def discover_tools(ctx: RunContext[Chat], keyword: str) -> dict[str, str]:
    """Busca herramientas por nombre o descripción y las habilita en la siguiente llamada."""
    # Escribe aquí tu código.
    # Busca keyword en CATALOG ({nombre: descripción}), agrega los nombres que encuentres a ctx.deps.loaded_tools
    # y devuelve esas coincidencias. available_tools (chat_agent.py) las enviará al modelo en la siguiente llamada.
    raise NotImplementedError("Paso 4: escribe discover_tools en paso4_descubrimiento.py")
