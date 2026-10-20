# Context workshop

Un chat local para practicar compactación, recuperación de archivos y descubrimiento de tools. Cada paso del taller tiene su archivo, y ahí escribes tu código:

| Archivo | Qué escribes |
|---|---|
| `paso2_disco.py` | `list_files`, `search_file`, `read_file` y `write_file` |
| `paso3_compactacion.py` | `compact`, con el mecanismo de compactación que elijas |
| `paso4_descubrimiento.py` | `discover_tools` |
| `paso5_subagente.py` | `ask_client`: un agente por cliente (extra) |

El resto ya funciona: `chat_agent.py` arma el agente y decide qué tools ve según los toggles; `base.py` tiene el estado del chat, el catálogo y las rutas seguras; `app.py` conecta el navegador; `customer_tools.py` contiene el catálogo simulado de atención al cliente. El frontend es una página HTML con JavaScript vanilla.

El frontend usa CSS propio inspirado en shadcn: tonos neutros, tarjetas, bordes suaves y botones simples. En pantallas amplias muestra conversación y contexto lado a lado; en pantallas pequeñas se apilan. No requiere React, Tailwind, fuentes externas ni instalación de componentes.

**Presentación del taller:** [`presentacion.html`](presentacion.html). Descárgala y ábrela en el navegador: flechas, espacio o clic para avanzar y `F` para pantalla completa. Imprimirla da una página por slide.

## Conversación muy larga: context rot en vivo

La conversación muy larga simula un análisis de procesos: una persona del equipo le pide al agente revisar cinco casos de soporte casi iguales para encontrar la falla que los produce, y le pasa las cinco conversaciones completas, una tras otra. Nébula Software queda a la mitad. Son 1,282 mensajes y unos 205 mil tokens según el proveedor. Vive en `datasets/conversacion-muy-larga/`, partida en archivos: `00-introduccion.json` y uno por cliente, de `01-despacho-ruiz-contadores.json` a `05-hotel-mirador.json`. Al cargarla, el servidor los junta en orden.

Pulsa **Cargar conversación muy larga**: se carga sin consumir API, con los toggles que tengas encendidos. Con todo apagado, pregunta: **"En el caso de Nébula Software, ¿cuántas tarjetas tienen una referencia que termina en un número mayor a 20?"** La respuesta correcta es 10.

| Modelo | Respuesta con la conversación muy larga |
|---|---|
| Haiku 5.5 | "No puedo responder" (3 de 3): dice que las tarjetas no son de ningún cliente |
| Sonnet 5.5 | Dice 10, pero mezcla tarjetas de otros clientes |

Las cinco preguntas trampa, con su respuesta correcta: [datasets/README.md](datasets/README.md). Pruebas del 17 de octubre de 2026 vía OpenRouter; los resultados varían entre intentos.

Para compactarla, enciende **Compactación**, y **Leer y escribir en disco** si quieres recuperar el original, y vuelve a cargarla: cada toggle abre un chat nuevo. Las 16 preguntas de `datasets/preguntas-y-respuestas.json` sirven para calificar qué conservó el resumen; el agente nunca las ve.

Cada pregunta manda los 205 mil tokens completos. Arriba de 100 mil tokens, Haiku 5.5 cobra su precio de contexto largo: unos 10 centavos de dólar por pregunta. Con Sonnet 5.5, unos 41.

## Tools de servicio al cliente

El catálogo tiene **80 tools**: diez por área de clientes, pedidos, envíos, pagos, devoluciones, suscripciones, soporte y productos. Cada una tiene nombre, descripción y parámetros propios; Pydantic genera los schemas y valida los argumentos. El catálogo ocupa alrededor de **30 mil tokens estimados** aunque aún no haya mensajes.

Enciende **Todas las tools** para mandar las 80 de servicio en cada llamada. Cambia a **Tools bajo demanda** para empezar solo con el buscador y comparar la barra: su definición ocupa alrededor de 67 tokens estimados. Los dos modos acceden a las mismas operaciones; lo que cambia es cuáles schemas recibe el modelo.

Las tools responden con texto fijo sobre los cinco clientes de la conversación muy larga, con las mismas cifras. Identificadores para probar:

| Cliente | Cuenta | Pedido | Reposición y guía | Pago duplicado | Devolución | Caso |
|---|---|---|---|---|---|---|
| Despacho Ruiz Contadores | CUS-L049 | ORD-2055 | ORD-2060, SHP-9924 | PAY-8850 | RET-0733 | SUP-3197 |
| Clínica Dental Sonrisa | CUS-L056 | ORD-2062 | ORD-2067, SHP-9931 | PAY-8857 | RET-0740 | SUP-3204 |
| Nébula Software | CUS-L042 | ORD-2048 | ORD-2053, SHP-9917 | PAY-8843 | RET-0726 | SUP-3190 |
| Agencia Pixel | CUS-L063 | ORD-2069 | ORD-2074, SHP-9938 | PAY-8864 | RET-0747 | SUP-3211 |
| Hotel Mirador | CUS-L070 | ORD-2076 | ORD-2081, SHP-9945 | PAY-8871 | RET-0754 | SUP-3218 |

El producto es `SKU-AUD-01`, los audífonos. Ningún cliente tiene suscripciones.

Prueba: **"Consulta el estado del pedido ORD-2048"**. Para una operación de escritura: **"Registra una solicitud de cancelación de ORD-2048: el cliente lo pidió por error"**.

Cada lectura busca el identificador que recibe y llena una plantilla de texto con los datos de ese cliente; si no existe, responde "No encontré…". Las escrituras registran la solicitud en memoria y la confirman con un folio, REQ-001, sin aplicar ningún cambio. El mismo handler sirve a las 80 tools; sus schemas son distintos. Así se puede explicar un catálogo grande sin implementar ochenta integraciones. Las lecturas de servicio se contabilizan como contexto buscado en la barra.

En carga completa, compactar el historial no elimina los schemas de las 84 tools: el segmento azul seguirá siendo grande. Para reducir esa parte hay que usar descubrimiento dinámico. Esta diferencia permite explicar por qué compactación y descubrimiento resuelven partes distintas del contexto.

**Verificación del catálogo (2026-10-12):** pasaron 17 pruebas. Una consulta real de `get_order_status` con las 84 tools cargadas devolvió el pedido en tránsito; la última llamada reportó 32,804 tokens de entrada. En la UI, cambiar a bajo demanda mostró una sola tool y 67 tokens estimados en sus definiciones. El consumo real depende del prompt y del historial de cada llamada.

## Correr

Python 3.11+ y una API key con crédito disponible. La configuración de ejemplo usa Claude Haiku 5.5 a través de OpenRouter: es barato y con la conversación muy larga se equivoca en vivo. Para comparar, cambia a `openrouter:anthropic/claude-sonnet-5.5`. Salvo la sección de context rot, las pruebas reales que cita este README se hicieron con Sonnet 4.6 y una versión anterior del dataset. Claude Code puede ayudar durante el taller; el servidor hace sus propias llamadas a la API.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Completa OPENROUTER_API_KEY en .env.
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Abre http://127.0.0.1:8000. `MODEL` permite cambiar el modelo sin modificar el código. La API key permanece en el servidor.

Para usar Anthropic directamente: configura `MODEL=anthropic:claude-haiku-5-5` y `ANTHROPIC_API_KEY` en `.env`. Reinicia el servidor si cambias la configuración. `.env` está excluido de Git; no lo compartas con el proyecto.

## Toggles

La página no tiene pasos fijos: cada toggle agrega algo a lo que el modelo recibe. Todo apagado es el chat básico. Cada cambio abre un chat nuevo.

| Toggle | Lo que el modelo recibe |
|---|---|
| Leer y escribir en disco | `list_files`, `search_file`, `read_file` y `write_file` |
| Todas las tools | Las 80 tools de servicio en cada llamada |
| Compactación | `compact_context` y los botones de compactar |
| Tools bajo demanda | Solo `discover_tools`; lo que encuentra se suma desde la siguiente llamada |
| Un agente por cliente | `ask_client` |

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

Las cuatro funciones son `write_file`, `list_files`, `search_file` y `read_file`, en `paso2_disco.py`. Listar devuelve rutas. `search_file` busca un texto en un archivo y devuelve solo las líneas que coinciden, con su número, como `grep`. `read_file` lee un rango de líneas, con un tope de 200 por llamada. Lo que regresa una tool entra completo al contexto: si leer cargara el archivo entero, un historial archivado de 1.3 MB volvería a llenar la ventana. Esa es la recuperación dinámica: el disco puede tener más información de la que enviamos en una llamada, y solo entra lo que hace falta. No usamos embeddings ni una base vectorial.

Cada chat tiene su carpeta bajo `workspace/<id>/`. Se muestra la ruta en la página para que puedas agregar o inspeccionar archivos manualmente. Las tools solo acceden a esa carpeta y a `archives/`, donde quedan los historiales compactados, junto al código. `write_file` reemplaza un archivo existente.

### 3. Compactar con o sin referencia

Enciende **Compactación**, y también **Leer y escribir en disco** para que el agente pueda leer el original archivado. Conversa varios turnos y usa uno de los botones. También puedes pedirlo en el chat:

> Compacta el historial con referencia al original.

> Compacta el historial sin referencia.

`compact_context` es la tool del agente. Solicita la operación; `respond` la aplica cuando termina el turno. Los botones llaman directamente a la misma función `compact` entre turnos. Así el historial nunca se corta a mitad de una llamada a tool.

`compact`, en `paso3_compactacion.py`, hace una llamada a un agente sin tools que genera el resumen. Luego **reemplaza** el historial por ese resumen.

| Opción | Qué queda en el contexto | Qué queda en disco |
|---|---|---|
| Sin referencia | Resumen | No se crea una copia del historial. |
| Con referencia | Resumen + ruta exacta al original | Historial completo en `archives/<id>.json`, en la carpeta del proyecto, junto a `app.py`. |

Con referencia, pide un detalle que no aparezca en el resumen: el agente lo busca en el original con `search_file` y lee solo esas líneas con `read_file`. Con la conversación muy larga y Haiku 5.5, recuperar los seriales dañados de Nébula costó unos 12 mil tokens de entrada (cuatro llamadas) en lugar de volver a cargar los 205 mil, y la respuesta citó las líneas del archivo. Buscar por texto encuentra detalles exactos (seriales, folios, fechas), no estructura: la pregunta de la sala de cada cliente sigue fallando después de compactar, porque la conversación no marca de qué cliente es cada tarjeta. Sin referencia, ese detalle puede perderse. Los archivos que el agente ya había escrito siguen existiendo en ambas opciones. Por eso, para comparar la pérdida causada por resumir, usa un dato que solo hayas mencionado en la conversación y que no esté guardado en otro archivo.

En **Contexto que se enviará al agente** puedes ver las instrucciones, las definiciones de tools activas y el historial en orden. Al compactar, el chat visible también se reemplaza: solo queda el mensaje de compactación, igual que en el historial que recibe el modelo. No hay compactación automática ni umbral oculto.

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

### 5. Extra: un agente por cliente

Para quien termine antes. Enciende **Un agente por cliente** y carga la conversación muy larga. En vez de juntar los cinco casos en un solo contexto, cada agente de cliente lee su propio archivo de `datasets/conversacion-muy-larga/` (256 mensajes, unos 41 mil tokens cada uno) y el agente principal empieza vacío.

Pide: **"Pregúntale al agente de cada cliente cuándo recibe su reposición. ¿Cuál la recibe primero?"** o **"¿Qué tan avanzada está la preparación de la sala de cada cliente?"**.

El código está en `paso5_subagente.py`. Con `ask_client(cliente, pregunta)`, el principal corre `client_agent`, otro agente Pydantic AI, con la conversación de ese cliente como `message_history`. Al principal solo le llega la respuesta. Si la pregunta es sobre varios clientes, le pregunta a cada uno; Pydantic AI corre esas llamadas en paralelo. Cada pregunta arranca de la conversación original del cliente: el sub-agente no acumula las preguntas anteriores.

| | Qué entra al contexto principal | Qué queda en disco |
|---|---|---|
| `ask_client` | La respuesta del agente del cliente | Nada nuevo: lee el archivo del cliente en `datasets/` |
| `search_file` y `read_file` sobre el JSON | Solo las líneas buscadas (el segmento naranja crece poco) | Sin cambios |

**Prueba real (2026-10-19, Haiku 5.5 vía OpenRouter):** las dos preguntas que fallan con los cinco casos juntos salieron bien 2 de 2: Nébula Software recibe primero (18 de octubre, de 09:00 a 11:30) y las cinco salas están igual, con 32 tarjetas y ninguna prueba ejecutada. Cada agente de cliente usó unos 41 mil tokens de entrada; los cinco suman los mismos ~205 mil de la conversación completa, pero repartidos. El principal usó entre 3 y 4 mil tokens de entrada y su contexto quedó en unos 2 mil. Cada pregunta tardó de 10 a 13 segundos.

Es la otra cara del context rot: la información no cambió, solo dejó de estar mezclada. Marcar los casos o separarlos en agentes también es ingeniería de contexto.

## Verificación sin consumir API

```sh
python -m pip install httpx
python -m unittest discover -s tests -v
```

Las pruebas usan `FunctionModel` de Pydantic AI para producir respuestas y llamadas a tools controladas. Verifican el loop real del agente, escritura y lectura, límites de rutas, ambos modos de compactación, recuperación del original, descubrimiento de tools y endpoints. No prueban la calidad de Claude al resumir ni su elección de tools: esas dos cosas se revisan con la API key en la demo.

Las pruebas del paso 5 simulan al principal y a los agentes de cliente con `FunctionModel`: verifican que cada agente ve solo la conversación de su cliente, que al principal solo llegan las respuestas y que cargar la conversación con el extra encendido apunta a los cinco archivos del dataset y deja al principal vacío. En la rama `solucion` pasan las 27 pruebas; en `main` fallan las de los pasos que todavía no escribes.

**Prueba real, 2026-10-12:** Claude Sonnet 4.6 vía OpenRouter respondió, descubrió `write_file`, escribió un archivo, compactó con referencia, leyó el archivo después de compactar y compactó sin referencia. También pasaron las 11 pruebas controladas. Se usaron datos sintéticos y carpetas temporales; esto confirma el flujo, no mide todavía calidad de resumen en conversaciones largas.

## Límites intencionales

Demo local con un único proceso. Conversaciones en memoria: reiniciar el servidor las pierde. Archivos en disco: sobreviven al reinicio. Cambiar un toggle o abrir un nuevo chat crea otra carpeta. No hay login, streaming, base de datos, Docker ni frontend compilado.

## Referencias del framework

- [Historial de mensajes](https://pydantic.dev/docs/ai/core-concepts/message-history/): `message_history` y `all_messages`.
- [PrepareTools](https://pydantic.dev/docs/ai/capabilities/prepare-tools/): seleccionar las definiciones que se envían al modelo.
- [Modelo de función para pruebas](https://pydantic.dev/docs/ai/api/pydantic-ai/models/function/).
- [OpenRouter](https://pydantic.dev/docs/ai/models/openrouter/): `OPENROUTER_API_KEY` y modelo `openrouter:anthropic/claude-haiku-5.5`.
