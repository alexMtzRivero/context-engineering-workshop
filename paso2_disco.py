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
    folder = ctx.deps.folder
    return sorted(
        str(path.relative_to(folder))
        for path in folder.rglob("*")
        # Solo archivos que siguen dentro de la carpeta: un enlace simbólico podría apuntar afuera.
        if path.is_file() and path.resolve().is_relative_to(folder.resolve())
        and keyword.casefold() in str(path.relative_to(folder)).casefold()
    )


def _lines(ctx: RunContext[Chat], name: str) -> list[str]:
    try:
        return file_path(ctx.deps, name).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        # ModelRetry le devuelve el error al modelo para que corrija la ruta.
        raise ModelRetry(f"No se pudo leer {name}: {error}") from error


def read_file(ctx: RunContext[Chat], name: str, start_line: int = 1, line_count: int = 100) -> str:
    """Lee un rango de líneas numeradas de un archivo de texto (máximo 200 por llamada).

    En un archivo grande, primero busca con search_file y lee solo alrededor de las líneas que encontró.
    """
    lines = _lines(ctx, name)
    start = max(start_line, 1)
    end = min(start + max(min(line_count, MAX_LINES), 1), len(lines) + 1)
    chunk, size = [], 0
    for number in range(start, end):
        line = f"{number}: {lines[number - 1]}"
        # Una sola línea enorme tampoco debe llenar el contexto.
        if chunk and size + len(line) > MAX_CHARS:
            end = number
            break
        chunk.append(line[:MAX_CHARS])
        size += len(line)
    header = f"{name}, líneas {start}-{end - 1} de {len(lines)}."
    if end - 1 < len(lines):
        header += " Hay más: pide otro rango o busca con search_file."
    return "\n".join([header, *chunk])


def search_file(ctx: RunContext[Chat], name: str, text: str, max_results: int = 20) -> str:
    """Busca un texto literal en un archivo, sin distinguir mayúsculas, y devuelve solo las líneas que coinciden.

    Cada resultado trae su número de línea para leer alrededor con read_file.
    """
    lines = _lines(ctx, name)
    needle = text.casefold()
    hits = [number for number, line in enumerate(lines, 1) if needle in line.casefold()]
    if not hits:
        return f"Sin coincidencias de «{text}» en {name}."
    shown = hits[:max(min(max_results, MAX_RESULTS), 1)]
    results = [f"{len(hits)} coincidencias de «{text}» en {name}, entre las líneas {hits[0]} y {hits[-1]}."]
    for number in shown:
        line = lines[number - 1]
        # Solo el fragmento alrededor de la coincidencia, no la línea completa.
        at = line.casefold().find(needle)
        start, end = max(at - SNIPPET, 0), at + len(text) + SNIPPET
        results.append(f"{number}: {'…' if start else ''}{line[start:end].strip()}{'…' if end < len(line) else ''}")
    if len(hits) > len(shown):
        results.append(f"Se muestran {len(shown)}. Busca un texto más específico o lee un rango con read_file.")
    return "\n".join(results)


def write_file(ctx: RunContext[Chat], name: str, content: str) -> str:
    """Guarda texto en una ruta relativa; reemplaza el contenido si el archivo existe."""
    try:
        path = file_path(ctx.deps, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Guardado: {name}"
    except OSError as error:
        raise ModelRetry(f"No se pudo guardar {name}: {error}") from error
