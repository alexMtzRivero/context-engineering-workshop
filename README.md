# Context workshop

Un chat local para practicar compactación, recuperación de archivos y descubrimiento de tools. Cada paso del taller tiene su archivo, y ahí escribes tu código:

| Archivo | Qué escribes |
|---|---|
| `paso2_disco.py` | `list_files`, `read_file` y `write_file` |
| `paso3_compactacion.py` | `compact`, con el mecanismo de compactación que elijas |
| `paso4_descubrimiento.py` | `discover_tools` |
| `paso5_subagente.py` | `delegate_research` y `ask_researcher` (extra) |

El resto ya funciona: `chat_agent.py` arma el agente y decide qué tools ve según los toggles; `base.py` tiene el estado del chat, el catálogo y las rutas seguras; `app.py` conecta el navegador; `customer_tools.py` contiene el catálogo simulado de atención al cliente. El frontend es una página HTML con JavaScript vanilla.

El frontend usa CSS propio inspirado en shadcn: tonos neutros, tarjetas, bordes suaves y botones simples. En pantallas amplias muestra conversación y contexto lado a lado; en pantallas pequeñas se apilan. No requiere React, Tailwind, fuentes externas ni instalación de componentes.

## Conversación larga para los estudiantes

[Dataset y guía de práctica](datasets/README.md): conversación ficticia de **256 mensajes**, unos **26 mil tokens estimados**, y 16 preguntas con respuestas esperadas separadas del historial. Incluye correcciones, acuerdos vigentes, pendientes y detalles antiguos para comprobar qué conserva la compactación.

En el chat, pulsa **Cargar conversación larga**; enciende sola la compactación y el disco. Se carga sin consumir API y queda lista para los botones de compactación. El mismo botón permite abrir otra copia original y comparar con y sin referencia. Los archivos fuente y las respuestas esperadas están fuera del workspace accesible al agente.

## Agente de servicio al cliente

El catálogo tiene **80 tools**: diez por área de clientes, pedidos, envíos, pagos, devoluciones, suscripciones, soporte y productos. Cada una tiene nombre, descripción y parámetros propios; Pydantic genera los schemas y valida los argumentos. El catálogo ocupa alrededor de **30 mil tokens estimados** aunque aún no haya mensajes.

Enciende **Todas las tools** para mandar las 80 de servicio en cada llamada. Cambia a **Tools bajo demanda** para empezar solo con el buscador y comparar la barra: su definición ocupa alrededor de 67 tokens estimados. Los dos modos acceden a las mismas operaciones; lo que cambia es cuáles schemas recibe el modelo.

Datos ficticios para probar:

| Entidad | Identificador |
|---|---|
| Cliente | CUS-001, Ana García, ana@example.com |
| Pedido | ORD-1001 |
| Envío | SHP-001 |
| Pago | PAY-001 |
| Devolución | RET-001 |
| Suscripción | SUB-001 |
| Ticket | TKT-001 |
| Producto | SKU-001, Audífonos Demo |

Prueba: **"Consulta el estado de mi pedido ORD-1001"**. Para una operación de escritura: **"Registra una solicitud de cancelación de ORD-1001 porque lo pedí por error"**.

Las lecturas filtran datos sintéticos por los parámetros. Las escrituras registran solicitudes en memoria y devuelven un folio REQ-001; no aplican el cambio comercial ni conectan servicios externos. El mismo handler simulado sirve a todas las tools; sus schemas son distintos. Así se puede explicar un catálogo grande sin implementar ochenta integraciones. Las lecturas de servicio se contabilizan como contexto buscado en la barra.

En carga completa, compactar el historial no elimina los schemas de las 84 tools: el segmento azul seguirá siendo grande. Para reducir esa parte hay que usar descubrimiento dinámico. Esta diferencia permite explicar por qué compactación y descubrimiento resuelven partes distintas del contexto.

**Verificación del catálogo (2026-10-12):** pasaron 17 pruebas. Una consulta real de `get_order_status` con las 84 tools cargadas devolvió el pedido en tránsito; la última llamada reportó 32,804 tokens de entrada. En la UI, cambiar a bajo demanda mostró una sola tool y 67 tokens estimados en sus definiciones. El consumo real depende del prompt y del historial de cada llamada.

## Correr

Python 3.11+ y una API key con crédito disponible. La configuración de ejemplo usa Claude a través de OpenRouter. Claude Code puede ayudar durante el taller; el servidor hace sus propias llamadas a la API.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Completa OPENROUTER_API_KEY en .env.
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Abre http://127.0.0.1:8000. `MODEL` permite cambiar el modelo sin modificar el código. La API key permanece en el servidor.

Para usar Anthropic directamente: configura `MODEL=anthropic:claude-sonnet-4-6` y `ANTHROPIC_API_KEY` en `.env`. Reinicia el servidor si cambias la configuración. `.env` está excluido de Git; no lo compartas con el proyecto.

## Toggles

La página no tiene pasos fijos: cada toggle agrega algo a lo que el modelo recibe. Todo apagado es el chat básico. Cada cambio abre un chat nuevo.

| Toggle | Lo que el modelo recibe |
|---|---|
| Leer y escribir en disco | `list_files`, `read_file` y `write_file` |
| Todas las tools | Las 80 tools de servicio en cada llamada |
| Compactación | `compact_context` y los botones de compactar |
| Tools bajo demanda | Solo `discover_tools`; lo que encuentra se suma desde la siguiente llamada |
| Sub-agente investigador | `delegate_research` y `ask_researcher` |

**Todas las tools** y **Tools bajo demanda** son dos formas de entregar el mismo catálogo, así que la página solo deja una encendida.

## Dónde escribir tu código

En `main`, las funciones de los pasos 2 a 5 están vacías y marcadas con `# Escribe aquí tu código.` Mientras no las escribas, la página te dice qué función falta y en qué archivo. El paso 1 funciona desde el inicio.

La rama `solucion` tiene todo resuelto. Para ver la respuesta de un paso:

```sh
git diff main solucion -- paso2_disco.py
```

Las pruebas sirven de checklist: en `main` fallan las de los pasos que todavía no escribes. Las del paso 3 validan la compactación con y sin referencia; si eliges otro mecanismo, ajústalas.

## Leer y explicar en este orden

### 1. Chat básico

Con todos los toggles apagados. La llamada central está en `respond`:

```python
result = await agent.run(message, message_history=chat.history, deps=chat)
chat.history = result.all_messages()
```

El modelo recibe un mensaje, responde y el servidor conserva el historial para la siguiente llamada. En este paso no recibe ninguna tool.

### 2. Leer y escribir en disco

Enciende **Leer y escribir en disco**. Cada cambio de toggle abre un chat nuevo. Prueba:

> Guarda en viaje.md: viajamos el 19 de octubre; la reunión es a las 17:10; el código de reserva es LIMA-4829.

> Lista los archivos relacionados con viaje y lee el que corresponda.

Las tres funciones son `write_file`, `list_files` y `read_file`, en `paso2_disco.py`. Listar devuelve rutas; leer carga el contenido de un archivo en el contexto. Esa es la recuperación dinámica: el disco puede tener más información de la que enviamos en una llamada. No usamos embeddings ni una base vectorial.

Cada chat tiene su carpeta bajo `workspace/<id>/`. Se muestra la ruta en la página para que puedas agregar o inspeccionar archivos manualmente. Las tools solo acceden a esa carpeta. `write_file` reemplaza un archivo existente.

### 3. Compactar con o sin referencia

Enciende **Compactación**, y también **Leer y escribir en disco** para que el agente pueda leer el original archivado. Conversa varios turnos y usa uno de los botones. También puedes pedirlo en el chat:

> Compacta el historial con referencia al original.

> Compacta el historial sin referencia.

`compact_context` es la tool del agente. Solicita la operación; `respond` la aplica cuando termina el turno. Los botones llaman directamente a la misma función `compact` entre turnos. Así el historial nunca se corta a mitad de una llamada a tool.

`compact`, en `paso3_compactacion.py`, hace una llamada a un agente sin tools que genera el resumen. Luego **reemplaza** el historial por ese resumen.

| Opción | Qué queda en el contexto | Qué queda en disco |
|---|---|---|
| Sin referencia | Resumen | No se crea una copia del historial. |
| Con referencia | Resumen + ruta exacta al original | Historial completo en `archives/<id>.json`. |

Con referencia, pide un detalle que no aparezca en el resumen: el agente puede usar `read_file` para recuperarlo del original. Sin referencia, ese detalle puede perderse. Los archivos que el agente ya había escrito siguen existiendo en ambas opciones. Por eso, para comparar la pérdida causada por resumir, usa un dato que solo hayas mencionado en la conversación y que no esté guardado en otro archivo.

En **Contexto que se enviará al agente** puedes ver las instrucciones, las definiciones de tools activas y el historial en orden. El chat visible mantiene los mensajes anteriores como apoyo a la demo; el modelo recibe el historial del servidor, no las burbujas del navegador. No hay compactación automática ni umbral oculto.

El contador antes/después mide bytes del historial JSON, incluyendo sus metadatos; no equivale al tamaño tokenizado del prompt. Los tokens reportados son el consumo real acumulado del agente en ese turno, incluidas las llamadas a tools; la llamada del resumidor se cobra aparte. En historiales muy cortos, el resumen puede ocupar más que el original. Resumir no garantiza conservar cada detalle.

### Barra de contexto

La barra de colores muestra el contexto activo para el **próximo turno**: tools (schemas disponibles, llamadas y resultados administrativos), chat actual, resumen, contexto buscado (resultados de `read_file`, `list_files` y las consultas de servicio) e instrucciones. El resumen se identifica con un metadato, no por el texto que escriba el usuario. También muestra cuántas tools están disponibles.

Cada segmento estima tokens usando 4 caracteres por token, sin llamar al proveedor ni contar timestamps y metadatos del historial. Es una aproximación didáctica, no el tokenizer de Claude. Los colores reparten el total estimado; no miden la fracción de la ventana máxima. El borrador sin enviar no se cuenta. Al compactar desaparecen del contexto las partes antiguas de chat y lecturas; al recuperar un archivo vuelve a crecer el segmento naranja. Los archivos guardados en disco no se cuentan hasta leerlos.

Debajo se muestra por separado la entrada real de la **última llamada del agente**, reportada por el proveedor. Esa cifra puede diferir de la barra, que incluye la respuesta recién generada y prepara el siguiente turno; también difiere del consumo acumulado de varias llamadas del mismo turno.

Dentro de la barra hay una vista única, siempre visible: **Contexto que se enviará al agente**. Muestra las entradas activas de Pydantic AI en JSON: instrucciones, tools y mensajes en orden. Tu próximo mensaje se añade al enviar. Se excluyen las tools todavía ocultas, los timestamps y las métricas internas. La vista se actualiza después de conversar, compactar o descubrir tools. Verificado en la UI y con una prueba de separación entre schemas ocultos y activos; pasan 18 pruebas.

### 4. Descubrimiento dinámico de tools

Enciende **Tools bajo demanda** y pide consultar un pedido o guardar un archivo.

Al principio el modelo solo ve `discover_tools`, en `paso4_descubrimiento.py`. Busca una palabra en el catálogo de nombres y descripciones. `available_tools`, con `PrepareTools`, incluye las definiciones descubiertas en la siguiente llamada del modelo. Abre **Tools enviadas al modelo** para ver el cambio. Una búsqueda amplia puede descubrir muchas herramientas; buscar un nombre exacto, como `get_order_status`, habilita solo esa operación.

Las tools descubiertas permanecen disponibles en ese chat hasta compactar. Compactar también limpia ese conjunto: el agente vuelve a descubrir lo que necesite. Es una búsqueda literal para explicar el mecanismo, no un buscador semántico ni MCP.

### 5. Extra: sub-agente investigador

Para quien termine antes. Enciende **Sub-agente investigador** y pide: **"Investiga el caso completo de CUS-001: pedido, envío, pago, devolución y ticket. ¿Hay algo pendiente?"**.

El código está en `paso5_subagente.py`. Con **Todas las tools** apagado, el agente principal no tiene las tools de servicio. Con `delegate_research` delega la tarea a `researcher`, otro agente Pydantic AI con contexto propio y 53 tools de solo lectura (51 de servicio más `list_files` y `read_file`). Los schemas y los resultados de esas consultas viven en el contexto del sub-agente. Al principal solo le llegan el informe, el `run_id` y la ruta del archivo. La conversación completa del sub-agente se guarda en `subagents/<run_id>.json`.

Después pregunta: **"¿Qué consultó el investigador para concluir lo de la devolución? Pregúntale a él, no adivines."**. Con `ask_researcher`, el principal **revive** al sub-agente: carga su historial desde disco, lo pasa como `message_history` y le hace la pregunta. El sub-agente responde con la memoria completa de su proceso y el archivo se actualiza con el nuevo intercambio.

| | Qué entra al contexto principal | Qué queda en disco |
|---|---|---|
| `delegate_research` | Informe breve + `run_id` + ruta | Conversación completa del sub-agente |
| `ask_researcher` | Respuesta a la pregunta | La misma conversación, con la pregunta añadida |
| `read_file` sobre el JSON | La conversación completa (el segmento naranja crece) | Sin cambios |

**Prueba real (2026-10-12, Claude Sonnet 4.6 vía OpenRouter):** la investigación de CUS-001 hizo que el sub-agente consumiera 92,062 tokens de entrada (8 mensajes, consultas en paralelo). El principal usó 6,366 en ese turno y su contexto quedó en unos 2,400 tokens estimados. Al revivirlo, el sub-agente respondió sin nuevas consultas cuáles 6 tools usó para concluir el estado de RET-001; esa llamada costó 28,308 tokens de entrada, porque reentra todo su historial. En una primera versión el informe venía con tablas y emojis; ahora se pide texto plano para otro agente, pero no se garantiza el límite de 120 palabras.

Es la misma idea que la compactación con referencia, aplicada a una tarea delegada: un resumen en el contexto y el original recuperable. La diferencia es que aquí el original se puede **interrogar** (revivir) en lugar de solo leer.

## Verificación sin consumir API

```sh
python -m pip install httpx
python -m unittest discover -s tests -v
```

Las pruebas usan `FunctionModel` de Pydantic AI para producir respuestas y llamadas a tools controladas. Verifican el loop real del agente, escritura y lectura, límites de rutas, ambos modos de compactación, recuperación del original, descubrimiento de tools y endpoints. No prueban la calidad de Claude al resumir ni su elección de tools: esas dos cosas se revisan con la API key en la demo.

Las pruebas del paso 5 simulan al principal y al sub-agente con `FunctionModel`: verifican que el resultado crudo de las tools no llega al principal, que investigar es solo lectura, que el archivo guarda la conversación completa y que el sub-agente revivido recibe su historial. En la rama `solucion` pasan las 23 pruebas; en `main` fallan las de los pasos que todavía no escribes.

**Prueba real, 2026-10-12:** Claude Sonnet 4.6 vía OpenRouter respondió, descubrió `write_file`, escribió un archivo, compactó con referencia, leyó el archivo después de compactar y compactó sin referencia. También pasaron las 11 pruebas controladas. Se usaron datos sintéticos y carpetas temporales; esto confirma el flujo, no mide todavía calidad de resumen en conversaciones largas.

## Límites intencionales

Demo local con un único proceso. Conversaciones en memoria: reiniciar el servidor las pierde. Archivos en disco: sobreviven al reinicio. Cambiar un toggle o abrir un nuevo chat crea otra carpeta. No hay login, streaming, base de datos, Docker ni frontend compilado.

## Referencias del framework

- [Historial de mensajes](https://pydantic.dev/docs/ai/core-concepts/message-history/): `message_history` y `all_messages`.
- [PrepareTools](https://pydantic.dev/docs/ai/capabilities/prepare-tools/): seleccionar las definiciones que se envían al modelo.
- [Modelo de función para pruebas](https://pydantic.dev/docs/ai/api/pydantic-ai/models/function/).
- [OpenRouter](https://pydantic.dev/docs/ai/models/openrouter/): `OPENROUTER_API_KEY` y modelo `openrouter:anthropic/claude-sonnet-4.6`.
