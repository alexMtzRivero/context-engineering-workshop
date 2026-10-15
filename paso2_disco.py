"""Paso 2: el agente guarda información en disco y la busca cuando la necesita, en vez de cargarla toda."""

from pydantic_ai import ModelRetry, RunContext

from base import Chat, file_path


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


def read_file(ctx: RunContext[Chat], name: str) -> str:
    """Lee el contenido de un archivo de texto por su ruta relativa."""
    try:
        return file_path(ctx.deps, name).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        # ModelRetry le devuelve el error al modelo para que corrija la ruta.
        raise ModelRetry(f"No se pudo leer {name}: {error}") from error


def write_file(ctx: RunContext[Chat], name: str, content: str) -> str:
    """Guarda texto en una ruta relativa; reemplaza el contenido si el archivo existe."""
    try:
        path = file_path(ctx.deps, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Guardado: {name}"
    except OSError as error:
        raise ModelRetry(f"No se pudo guardar {name}: {error}") from error
