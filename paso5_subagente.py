"""Extra: un agente por cliente. Cada uno tiene solo la conversación de su caso; el principal le hace preguntas.

Cada cliente tiene su conversación en su propio archivo (datasets/conversacion-muy-larga/0X-<cliente>.json);
su agente la lee como historial y al principal solo llegan las respuestas.
"""

from pydantic_ai import Agent, ModelRetry, RunContext

from base import MODEL, Chat, read_conversation

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
    matches = []
    for name in chat.clients:
        if client.lower() in name.lower():
            matches.append(name)
    if len(matches) == 1:
        return matches[0]
    known_clients = ", ".join(chat.clients) or "ninguno"
    raise ModelRetry(f"No reconozco a «{client}». Clientes con agente: {known_clients}.")


async def ask_client(ctx: RunContext[Chat], client: str, question: str) -> str:
    """Pregunta al agente de un cliente por su caso. Ese agente tiene la conversación completa del cliente;
    tú solo recibes su respuesta. Si la pregunta es sobre varios clientes, pregúntale a cada uno."""
    # Escribe aquí tu código.
    # 1. find_client(ctx.deps, client) da el nombre exacto; ctx.deps.clients[nombre] es el archivo de su conversación.
    # 2. Léelo con read_conversation(archivo) y pásalo a client_agent.run(question, message_history=...).
    # 3. Agrega a ctx.deps.subagent_runs un dict con client, question, answer, transcript, messages e input_tokens
    #    para que la página lo muestre, y devuelve solo la respuesta: es lo único que entra al contexto del principal.
    raise NotImplementedError("Extra: escribe ask_client en paso5_subagente.py")
