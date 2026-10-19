"""Extra: un agente por cliente. Cada uno tiene solo la conversación de su caso; el principal le hace preguntas.

Las conversaciones de los clientes viven en disco (clientes/<cliente>.json) y en el contexto de cada sub-agente;
al principal solo llegan las respuestas.
"""

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.messages import ModelMessagesTypeAdapter

from base import MODEL, Chat, file_path

# Un solo agente, que se corre con el historial de un cliente distinto en cada pregunta. No tiene tools,
# así que no razona (como el principal sin tools).
client_agent = Agent(
    MODEL,
    instructions=(
        "Eres el agente del caso de un solo cliente: tu historial es su conversación de soporte completa. "
        "El agente principal te pregunta por ese caso. Responde con los datos exactos de tu conversación "
        "(fechas, identificadores, montos y nombres) y, si un dato cambió, da el vigente. "
        "Si algo no está en tu conversación, dilo. Los datos son ficticios. "
        "Tu respuesta la lee otro agente: texto plano y breve, sin tablas, títulos ni emojis."
    ),
    model_settings={"thinking": False},
    defer_model_check=True,
)


def find_client(chat: Chat, client: str) -> str:
    """Encuentra el cliente por nombre completo o parcial, sin distinguir mayúsculas."""
    matches = [name for name in chat.clients if client.casefold() in name.casefold()]
    if len(matches) != 1:
        raise ModelRetry(f"No reconozco a «{client}». Clientes con agente: {', '.join(chat.clients) or 'ninguno'}.")
    return matches[0]


async def ask_client(ctx: RunContext[Chat], client: str, question: str) -> str:
    """Pregunta al agente de un cliente por su caso. Ese agente tiene la conversación completa del cliente;
    tú solo recibes su respuesta. Si la pregunta es sobre varios clientes, pregúntale a cada uno."""
    name = find_client(ctx.deps, client)
    reference = ctx.deps.clients[name]
    history = ModelMessagesTypeAdapter.validate_json(file_path(ctx.deps, reference).read_bytes())
    # Cada pregunta arranca de la conversación del cliente: el sub-agente no acumula preguntas anteriores.
    result = await client_agent.run(question, message_history=history)
    run = {
        "client": name, "question": question, "answer": result.output, "transcript": reference,
        "messages": len(history), "input_tokens": result.usage.input_tokens,
    }
    ctx.deps.subagent_runs.append(run)
    ctx.deps.events.append(f"Agente de {name}: {run['messages']} mensajes, {run['input_tokens']} tokens de entrada")
    # Esto es lo único que entra al contexto del agente principal.
    return result.output
