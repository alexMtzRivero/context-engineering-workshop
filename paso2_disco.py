"""Paso 2: el agente guarda información en disco y la busca cuando la necesita, en vez de cargarla toda."""

from pydantic_ai import ModelRetry, RunContext

from base import Chat, file_path

# file_path(ctx.deps, nombre) convierte una ruta relativa en una ruta segura dentro de la carpeta del chat.
# Si algo falla, lanza ModelRetry("...") para que el modelo reciba el error y lo intente de nuevo.


def list_files(ctx: RunContext[Chat], keyword: str = "") -> list[str]:
    """Lista rutas de archivos que contienen keyword; no carga sus contenidos."""
    # Escribe aquí tu código.
    # Devuelve las rutas relativas dentro de ctx.deps.folder que contienen keyword.
    raise NotImplementedError("Paso 2: escribe list_files en paso2_disco.py")


def read_file(ctx: RunContext[Chat], name: str) -> str:
    """Lee el contenido de un archivo de texto por su ruta relativa."""
    # Escribe aquí tu código.
    # Devuelve el texto del archivo; lo que regreses entra completo al contexto.
    raise NotImplementedError("Paso 2: escribe read_file en paso2_disco.py")


def write_file(ctx: RunContext[Chat], name: str, content: str) -> str:
    """Guarda texto en una ruta relativa; reemplaza el contenido si el archivo existe."""
    # Escribe aquí tu código.
    # Crea las carpetas que falten, guarda content y confirma con un texto corto.
    raise NotImplementedError("Paso 2: escribe write_file en paso2_disco.py")
