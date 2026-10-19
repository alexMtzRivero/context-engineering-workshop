"""Paso 2: el agente guarda información en disco y la busca cuando la necesita, en vez de cargarla toda."""

from pydantic_ai import ModelRetry, RunContext

from base import Chat, file_path

# file_path(ctx.deps, nombre) convierte una ruta relativa en una ruta segura dentro de la carpeta del chat.
# Si algo falla, lanza ModelRetry("...") para que el modelo reciba el error y lo intente de nuevo.

# Topes por llamada: lo que devuelve una tool entra completo al contexto.
MAX_LINES = 200
MAX_CHARS = 40_000  # unos 10 mil tokens
MAX_RESULTS = 30
SNIPPET = 160  # caracteres a cada lado de una coincidencia


def list_files(ctx: RunContext[Chat], keyword: str = "") -> list[str]:
    """Lista rutas de archivos que contienen keyword; no carga sus contenidos."""
    # Escribe aquí tu código.
    # Devuelve las rutas relativas dentro de ctx.deps.folder que contienen keyword.
    raise NotImplementedError("Paso 2: escribe list_files en paso2_disco.py")


def read_file(ctx: RunContext[Chat], name: str, start_line: int = 1, line_count: int = 100) -> str:
    """Lee un rango de líneas numeradas de un archivo de texto (máximo 200 por llamada).

    En un archivo grande, primero busca con search_file y lee solo alrededor de las líneas que encontró.
    """
    # Escribe aquí tu código.
    # Devuelve las líneas desde start_line, numeradas ("15: texto"), sin pasar de MAX_LINES ni de MAX_CHARS.
    # Lo que regreses entra completo al contexto: si devuelves el archivo entero, un historial archivado
    # vuelve a llenar la ventana. Avisa si quedan más líneas.
    raise NotImplementedError("Paso 2: escribe read_file en paso2_disco.py")


def search_file(ctx: RunContext[Chat], name: str, text: str, max_results: int = 20) -> str:
    """Busca un texto literal en un archivo, sin distinguir mayúsculas, y devuelve solo las líneas que coinciden.

    Cada resultado trae su número de línea para leer alrededor con read_file.
    """
    # Escribe aquí tu código.
    # Como grep: cuenta las líneas que contienen text y devuelve hasta max_results (nunca más de MAX_RESULTS),
    # cada una con su número y solo SNIPPET caracteres alrededor de la coincidencia.
    raise NotImplementedError("Paso 2: escribe search_file en paso2_disco.py")


def write_file(ctx: RunContext[Chat], name: str, content: str) -> str:
    """Guarda texto en una ruta relativa; reemplaza el contenido si el archivo existe."""
    # Escribe aquí tu código.
    # Crea las carpetas que falten, guarda content y confirma con un texto corto.
    raise NotImplementedError("Paso 2: escribe write_file en paso2_disco.py")
