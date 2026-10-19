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
    # 1. Leer la conversación de ese cliente: su propio archivo del dataset.
    name = find_client(ctx.deps, client)
    conversation_file = ctx.deps.clients[name]
    conversation = read_conversation(conversation_file)

    # 2. Preguntarle a su agente, con esa conversación como historial.
    #    Cada pregunta arranca de la conversación original: el agente no acumula preguntas anteriores.
    result = await client_agent.run(question, message_history=conversation)
    answer = result.output

    # 3. Avisar a la página quién respondió y cuánto contexto usó; esto no entra al contexto del principal.
    ctx.deps.subagent_runs.append({
        "client": name,
        "question": question,
        "answer": answer,
        "transcript": f"datasets/{conversation_file.parent.name}/{conversation_file.name}",
        "messages": len(conversation),
        "input_tokens": result.usage.input_tokens,
    })
    ctx.deps.events.append(f"Agente de {name}: {len(conversation)} mensajes, {result.usage.input_tokens} tokens de entrada")

    # Lo único que entra al contexto del agente principal es la respuesta.
    return answer
