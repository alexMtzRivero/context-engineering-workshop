"""Extra: el principal delega una investigación a un sub-agente con su propio contexto.

Las tools de lectura y sus resultados viven en el contexto del sub-agente; al principal solo llega el informe.
La conversación completa queda en disco para revivir al sub-agente y preguntarle por su proceso.
"""

from uuid import uuid4

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.messages import ModelMessagesTypeAdapter

from base import MODEL, Chat, file_path
from customer_tools import CUSTOMER_TOOLS, READ_TOOL_NAMES
from paso2_disco import list_files, read_file

# Otro agente, con sus propias instrucciones y solo tools de lectura.
researcher = Agent(
    MODEL,
    deps_type=Chat,
    instructions=(
        "Eres un sub-agente investigador. Recibes una tarea del agente principal. "
        "Consulta con las tools de solo lectura lo necesario para resolverla; no registras solicitudes ni cambios. "
        "Usa solo datos devueltos por las tools; los datos son ficticios. "
        "Tu respuesta final la lee otro agente, no el cliente: texto plano, sin tablas, títulos ni emojis, "
        "máximo 120 palabras, con hallazgos, identificadores consultados y dudas abiertas."
    ),
    tools=[list_files, read_file, *(tool for tool in CUSTOMER_TOOLS if tool.name in READ_TOOL_NAMES)],
    defer_model_check=True,
)


def save_run(chat: Chat, run_id: str, task: str, result, revived: bool) -> dict:
    """Guarda la conversación completa del sub-agente en disco y la reporta a la página."""
    reference = f"subagents/{run_id}.json"
    path = file_path(chat, reference)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(ModelMessagesTypeAdapter.dump_json(result.all_messages(), indent=2))
    run = {
        "run_id": run_id, "task": task, "report": result.output, "transcript": reference, "revived": revived,
        "messages": len(result.all_messages()), "input_tokens": result.usage.input_tokens,
    }
    chat.subagent_runs.append(run)
    chat.events.append(
        f"Sub-agente {run_id}{' revivido' if revived else ''}: {run['messages']} mensajes, "
        f"{run['input_tokens']} tokens de entrada; conversación en {reference}"
    )
    # Esto es lo único que entra al contexto del agente principal.
    return {"run_id": run_id, "report": result.output, "transcript": reference}


async def delegate_research(ctx: RunContext[Chat], task: str) -> dict:
    """Delega una investigación a un sub-agente que consulta las tools de lectura de servicio
    (clientes, pedidos, envíos, pagos, devoluciones, suscripciones, soporte y productos).
    Devuelve su informe y su run_id."""
    # Escribe aquí tu código.
    # Corre researcher con la tarea, sin historial previo, y guarda su conversación con save_run.
    # Usa un run_id corto y alfanumérico, por ejemplo uuid4().hex[:8].
    raise NotImplementedError("Extra: escribe delegate_research en paso5_subagente.py")


async def ask_researcher(ctx: RunContext[Chat], run_id: str, question: str) -> dict:
    """Revive a un sub-agente anterior con toda su conversación para preguntarle por su proceso."""
    # Escribe aquí tu código.
    # Lee subagents/<run_id>.json con ModelMessagesTypeAdapter.validate_json, pásalo como message_history
    # a researcher junto con la pregunta y guarda la conversación actualizada con save_run.
    # Si el run_id no existe, lanza ModelRetry para que el modelo use uno válido.
    raise NotImplementedError("Extra: escribe ask_researcher en paso5_subagente.py")
