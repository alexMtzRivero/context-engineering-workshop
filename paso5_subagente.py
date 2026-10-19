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
    # Sin message_history: el sub-agente arranca con un contexto vacío y comparte solo la carpeta.
    result = await researcher.run(task, deps=ctx.deps)
    return save_run(ctx.deps, uuid4().hex[:8], task, result, revived=False)


async def ask_researcher(ctx: RunContext[Chat], run_id: str, question: str) -> dict:
    """Revive a un sub-agente anterior con toda su conversación para preguntarle por su proceso."""
    path = file_path(ctx.deps, f"subagents/{run_id}.json")
    # isalnum impide que el run_id se use para leer fuera de subagents/.
    if not run_id.isalnum() or not path.is_file():
        raise ModelRetry(f"No existe el sub-agente {run_id}. Usa el run_id que devolvió delegate_research.")
    # Revivir es volver a pasarle su historial completo como message_history.
    history = ModelMessagesTypeAdapter.validate_json(path.read_bytes())
    result = await researcher.run(question, message_history=history, deps=ctx.deps)
    return save_run(ctx.deps, run_id, question, result, revived=True)
