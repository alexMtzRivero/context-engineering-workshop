# Práctica: compactar una conversación larga

Dataset completamente ficticio: **256 mensajes, 128 intercambios y 103,705 caracteres** de conversación, alrededor de **26 mil tokens estimados** de contenido. El proveedor puede contar una cantidad diferente. No contiene datos de personas reales ni registra acciones comerciales.

- `conversacion-larga.json`: historial con `role` y `content`, listo para cargar.
- `conversacion-larga.md`: el mismo historial en formato de lectura.
- `preguntas-y-respuestas.json`: 16 preguntas y respuestas esperadas para revisar resultados. Este archivo no se carga al agente.

## Caso

Valeria Ortiz coordina Aula Norte y compró 40 audífonos para un taller. Hay unidades faltantes, dos dañadas y un cobro duplicado. La conversación intercala los acuerdos del caso con 32 consultas de preparación de un laboratorio. Cada consulta tiene un procedimiento y un identificador propio.

Los acuerdos cambian: hay una dirección anterior, otra ventana de entrega, un contacto sustituido y una cotización de recogida descartada. El agente debe conservar el estado vigente y distinguir solicitudes de operaciones ya realizadas. Algunos detalles antiguos, como seriales y referencias internas, son deliberadamente difíciles de incluir en un resumen de 150 palabras.

Es un **caso histórico independiente** de los registros simulados de las tools comerciales. Para esta práctica las preguntas se refieren a lo hablado y acordado en esta conversación.

## En el chat

1. Primero, con todos los toggles apagados, carga la conversación y haz una de las preguntas: así ves cómo responde el agente con todo el contexto. Después enciende **Compactación** y **Leer y escribir en disco** (el disco hace falta para leer el original archivado) y deja **Todas las tools** apagado para que los schemas no tapen el tamaño de la conversación. Cada toggle abre un chat nuevo.
2. Pulsa **Cargar conversación larga**. Abre un chat nuevo con los 256 mensajes en el historial. Cargarlo no llama a ningún modelo. El botón se puede volver a usar para empezar desde el mismo original.
3. Anota el tamaño del chat en la barra. Inspecciona las instrucciones, tools e historial en la vista de contexto.
4. Pulsa **Compactar sin referencia**. Esta acción hace una llamada a la API. Inspecciona el resumen y el nuevo tamaño del contexto.
5. Pregunta, por ejemplo: **"Según lo acordado en esta conversación, ¿cuál es la ventana de entrega vigente y cuáles se descartaron?"**. Luego pregunta por un detalle: **"Según lo hablado, ¿qué formato y duración de prueba se acordaron en la tarjeta MIC-48K-16?"**. Comprueba primero si ese detalle está en el resumen.
6. Guarda tus observaciones y vuelve a **Cargar conversación larga**, creando otra copia original. Pulsa **Compactar con referencia**.
7. Formula las mismas preguntas. Para un dato omitido en el resumen, pide: **"Lee el historial original usando su referencia y recupera el dato. No lo inventes."**. Observa el segmento naranja cuando se recupera el archivo.

El dataset fuente se mantiene en `datasets/`, **fuera de la carpeta que pueden leer las tools del chat**. Cargarlo no copia ese archivo al workspace. En el modo sin referencia no se crea una copia recuperable del historial; en el modo con referencia se archiva el original dentro de la carpeta del chat. Las respuestas esperadas tampoco están disponibles para el agente.

## Cómo comparar

Usa las 16 preguntas de `preguntas-y-respuestas.json`. Para cada ejecución, registra:

| Pregunta | Resultado (0 / 0.5 / 1) | Fuente de la respuesta | Observación |
|---|---|---|---|
| Identificador de la pregunta | 1: todos los elementos correctos; 0.5: parte correcta sin contradicción; 0: contradice o inventa | Resumen / original recuperado / dato no disponible | Qué omitió o confundió |

Revisa especialmente las correcciones, restricciones y pendientes. Medir cuánto se redujo el contexto no basta si el resumen mantiene una fecha descartada o inventa un abono ya realizado.

La compactación es variable: no se garantiza qué detalle omitirá el modelo. Las dos ejecuciones pueden producir resúmenes diferentes. Conserva los resúmenes y anota cómo obtuvo cada respuesta. Recuperar el archivo completo puede volver a aumentar mucho el contexto; compactar nuevamente permite discutir ese intercambio.

**Prueba real del 12 de octubre de 2026:** con Claude Sonnet 4.6 vía OpenRouter, el contexto activo, con las tools bajo demanda, pasó de 26,250 a 852 tokens estimados después de compactar con referencia. El archivo original conservó los 256 mensajes. El resumen mantuvo los acuerdos principales y varios identificadores; omitió detalles de las pruebas técnicas. Estos resultados corresponden a una ejecución, no a una reducción garantizada. Los dos modos también se verificaron con pruebas controladas, dentro de una suite de 20 pruebas.

## Conversación muy larga

`conversacion-muy-larga.json` mete este mismo caso entre siete casos casi idénticos (unos 326 mil tokens) para ver el deterioro en vivo. Lo genera `generar_muy_larga.py`; las preguntas y resultados están en el README principal, sección "Conversación muy larga".

## Cargarlo desde Python

El endpoint de `app.py` usa esta conversión mínima:

```python
import json
from pathlib import Path
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

messages = json.loads(Path("datasets/conversacion-larga.json").read_text())["messages"]
history = [
    ModelRequest(parts=[UserPromptPart(content=m["content"])])
    if m["role"] == "user" else ModelResponse(parts=[TextPart(content=m["content"])])
    for m in messages
]
# await agent.run("¿Qué acordamos?", message_history=history, deps=chat)
```
