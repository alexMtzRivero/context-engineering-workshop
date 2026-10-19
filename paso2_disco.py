"""Paso 2: el agente guarda información en disco y la busca cuando la necesita, en vez de cargarla toda."""

from pydantic_ai import ModelRetry, RunContext

from base import Chat, file_path

# Topes por llamada: lo que devuelve una tool entra completo al contexto.
MAX_LINES = 200
MAX_CHARS = 40_000  # unos 10 mil tokens
MAX_RESULTS = 30
SNIPPET = 160  # caracteres a cada lado de una coincidencia


def list_files(ctx: RunContext[Chat], keyword: str = "") -> list[str]:
    """Lista rutas de archivos que contienen keyword; no carga sus contenidos."""
    # Equivale a: find . -type f -iname "*keyword*"
    folder = ctx.deps.folder
    found = []
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        # Un enlace simbólico podría apuntar fuera de la carpeta del chat.
        if not path.resolve().is_relative_to(folder.resolve()):
            continue
        relative_path = str(path.relative_to(folder))
        if keyword.lower() in relative_path.lower():
            found.append(relative_path)
    return sorted(found)


def read_lines(ctx: RunContext[Chat], name: str) -> list[str]:
    """Lee un archivo de la carpeta del chat y lo devuelve separado en líneas."""
    try:
        text = file_path(ctx.deps, name).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        # ModelRetry le devuelve el error al modelo para que corrija la ruta.
        raise ModelRetry(f"No se pudo leer {name}: {error}") from error
    return text.splitlines()


def read_file(ctx: RunContext[Chat], name: str, start_line: int = 1, line_count: int = 100) -> str:
    """Lee un rango de líneas numeradas de un archivo de texto (máximo 200 por llamada).

    En un archivo grande, primero busca con search_file y lee solo alrededor de las líneas que encontró.
    """
    # Equivale a: cat -n archivo | sed -n '14044,14067p', con un tope de líneas y de caracteres.
    lines = read_lines(ctx, name)
    total_lines = len(lines)

    # 1. Qué rango leer: nunca más de MAX_LINES líneas.
    first_line = max(start_line, 1)
    lines_to_read = min(line_count, MAX_LINES)
    if lines_to_read < 1:
        lines_to_read = 1
    last_line = min(first_line + lines_to_read - 1, total_lines)

    # 2. Juntar las líneas numeradas hasta llegar al tope de caracteres.
    page = []
    characters = 0
    for number in range(first_line, last_line + 1):
        line = f"{number}: {lines[number - 1]}"
        # Una sola línea enorme tampoco debe llenar el contexto.
        if page and characters + len(line) > MAX_CHARS:
            last_line = number - 1
            break
        page.append(line[:MAX_CHARS])
        characters += len(line)

    # 3. Decirle al agente qué leyó y si quedó algo pendiente.
    header = f"{name}, líneas {first_line}-{last_line} de {total_lines}."
    if last_line < total_lines:
        header += " Hay más: pide otro rango o busca con search_file."
    return "\n".join([header] + page)


def search_file(ctx: RunContext[Chat], name: str, text: str, max_results: int = 20) -> str:
    """Busca un texto literal en un archivo, sin distinguir mayúsculas, y devuelve solo las líneas que coinciden.

    Cada resultado trae su número de línea para leer alrededor con read_file.
    """
    # Equivale a: grep -n -i -F "texto" archivo | head -30, con cada línea recortada alrededor del texto.
    lines = read_lines(ctx, name)
    wanted = text.lower()

    # 1. Como grep: anotar el número de cada línea que contiene el texto.
    matching_lines = []
    for number, line in enumerate(lines, start=1):
        if wanted in line.lower():
            matching_lines.append(number)

    if not matching_lines:
        return f"Sin coincidencias de «{text}» en {name}."

    # 2. Mostrar pocas: el total y las primeras, cada una recortada alrededor de la coincidencia.
    results_to_show = min(max_results, MAX_RESULTS)
    if results_to_show < 1:
        results_to_show = 1
    first, last = matching_lines[0], matching_lines[-1]
    report = [f"{len(matching_lines)} coincidencias de «{text}» en {name}, entre las líneas {first} y {last}."]
    for number in matching_lines[:results_to_show]:
        report.append(f"{number}: {fragment_around(lines[number - 1], wanted)}")

    if len(matching_lines) > results_to_show:
        report.append(f"Se muestran {results_to_show}. Busca un texto más específico o lee un rango con read_file.")
    return "\n".join(report)


def fragment_around(line: str, wanted: str) -> str:
    """El pedazo de la línea alrededor de la coincidencia, no la línea completa."""
    position = line.lower().find(wanted)
    start = max(position - SNIPPET, 0)
    end = position + len(wanted) + SNIPPET
    fragment = line[start:end].strip()
    if start > 0:
        fragment = "…" + fragment
    if end < len(line):
        fragment = fragment + "…"
    return fragment


def write_file(ctx: RunContext[Chat], name: str, content: str) -> str:
    """Guarda texto en una ruta relativa; reemplaza el contenido si el archivo existe."""
    # Equivale a: echo "contenido" > archivo
    try:
        path = file_path(ctx.deps, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as error:
        raise ModelRetry(f"No se pudo guardar {name}: {error}") from error
    return f"Guardado: {name}"
