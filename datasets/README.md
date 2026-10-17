# Datasets del taller

Dos conversaciones artificiales entre una clienta y un agente de servicio al cliente. Todo es ficticio: no hay personas reales, no se registraron acciones comerciales y los correos usan dominios de ejemplo.

| Archivo | Qué es |
|---|---|
| `conversacion-larga.json` | El caso de Aula Norte: 256 mensajes, listo para cargar |
| `conversacion-larga.md` | El mismo historial en formato de lectura |
| `preguntas-y-respuestas.json` | 16 preguntas con su respuesta esperada para calificar resúmenes; nunca se carga al agente |
| `conversacion-muy-larga.json` | El mismo caso escondido entre siete casos casi idénticos: 2,048 mensajes |
| `generar_muy_larga.py` | Genera la conversación muy larga a partir de la larga |

## Conversación larga: el caso de Aula Norte

Valeria Ortiz coordina Aula Norte (cuenta CUS-L042) y compró 40 audífonos (pedido ORD-2048) para un taller del 19 de octubre de 2026. A lo largo de la conversación resuelve tres frentes con el agente:

- **Equipo incompleto.** Llegaron 36 audífonos: 34 funcionan, 2 están dañados (seriales AO-2048-009 y AO-2048-027) y faltan 4. Se acuerda reponer 6 unidades con el pedido ORD-2053 y la guía SHP-9917. Los dañados se recogen con la etiqueta RET-0726, propuesta para el 20 de octubre de 10:00 a 13:00, a costo cero por la excepción EXC-4402 que autorizó Sonia Méndez. Una cotización de 75 MXN quedó descartada.
- **Entrega.** La ventana vigente es el 18 de octubre de 09:00 a 11:30, en Avenida del Laboratorio 240, edificio B, puerta 3 para proveedores. El día 17 y las 12:30 quedaron descartados. Recibe Paula Ramos; el correo operativo es logistica@aula.example. Mario León y coordinacion@aula.example quedaron como antecedentes. La frase de acceso de recepción es LUNA-58. Diego Salas, de logística, debe confirmar antes del 15 de octubre a las 17:00; el caso es SUP-3190 (SUP-3106 queda como antecedente) y la referencia interna de su cola es MESA-27.
- **Cobro duplicado.** PAY-8842 es el pago válido y PAY-8843, por 31,644.80 MXN, el duplicado. La devolución va al medio de pago original, sin crédito ni cupón, con el folio FIN-6631; Laura Peña debe aportar la evidencia. No hay confirmación de abono.

Entre esos acuerdos se intercalan **32 consultas para preparar un laboratorio**, una por puesto (01 a 32). Son cuatro puestos por equipo: audífonos, cámara, router, dock USB, teclado, monitor, micrófono USB y almacenamiento USB. Cada consulta termina en una tarjeta con referencia propia, por ejemplo LAB-BT-04 en el puesto 01. El número de la referencia casi nunca coincide con el del puesto: MIC-48K-16 está en el puesto 27 y la tarjeta del puesto 16 es DOCK-CAB-14. Solo coincide NET-CAN-11. Es una trampa intencional.

Los acuerdos cambian durante la conversación: hay una dirección anterior, otra ventana de entrega, un contacto sustituido y una cotización descartada. Sirve para ver si un resumen conserva el estado vigente y no un dato viejo.

Tamaño: 256 mensajes (128 intercambios) y 103,705 caracteres. La página estima unos 26 mil tokens; el proveedor reporta unos 41 mil con Claude 5.5.

## Conversación muy larga: ocho aulas casi iguales

Repite el caso ocho veces, una por aula, en este orden: Sur, Este, Oeste, Centro, **Norte**, Poniente, Oriente y Bajío. Aula Norte, el caso original, queda en el bloque 5, a la mitad.

Cada copia cambia el aula, las seis personas, los números de todos los identificadores (ORD-2048 pasa a ORD-2055, ORD-2062...), las fechas, las horas, el monto del cobro duplicado y el número de la dirección. Se conservan las cantidades de equipo y los puestos 01 a 32, así que cada puesto tiene ocho tarjetas casi iguales, una por aula. Por ejemplo, el puesto 16 tiene DOCK-CAB-21, DOCK-CAB-28, DOCK-CAB-35, DOCK-CAB-42, DOCK-CAB-14, DOCK-CAB-49, DOCK-CAB-56 y DOCK-CAB-63.

Esos casi duplicados son los distractores que deterioran las respuestas. Tamaño: 2,048 mensajes, unos 830 mil caracteres; la página estima unos 208 mil tokens y el proveedor reporta unos 326 mil. Se regenera con `python datasets/generar_muy_larga.py`.

## Preguntas trampa

Con todos los toggles apagados, carga la conversación y haz la pregunta. Estas cinco fallaron con **Claude Haiku 5.5** en la conversación muy larga:

| # | Pregunta | Respuesta correcta | Conversación larga | Conversación muy larga |
|---|---|---|---|---|
| 1 | En el caso de Aula Norte, ¿cuántas tarjetas tienen una referencia que termina en un número mayor a 20? | 10 | Bien, 3 de 3 | Mal, 4 de 4: "no puedo responder", dice que las tarjetas no son de ningún aula |
| 2 | En el caso de Aula Norte, ¿en qué tarjetas coincide el número final de la referencia con el número del puesto? | Solo NET-CAN-11, puesto 11 | Bien | Mal, 2 de 2: no separa las tarjetas de Aula Norte de las demás |
| 3 | En el caso de Aula Norte, lista las tarjetas del micrófono USB con su puesto. | MIC-GAIN-18 (25), MIC-MON-21 (26), MIC-48K-16 (27), MIC-TEST-08 (28) | Bien | Mal, 2 de 2: dice que esas tarjetas no son de Aula Norte |
| 4 | En toda la conversación, ¿cuál fue la sexta tarjeta que se registró para el puesto 16 y de qué aula era? | DOCK-CAB-49, de Aula Poniente | No aplica | Mal en 3 de 4: respondió DOCK-CAB-56 y una vez se saltó justo la de Aula Norte |
| 5 | En toda la conversación, ¿cuál fue la cuarta aula en presentarse y quién la coordina? | Aula Centro, Rosa Medina | No aplica | Mal en 1 de 2: respondió Aula Norte y Valeria Ortiz |

Por qué son trampa:

1. Contar exige revisar todo el bloque de Aula Norte sin mezclarlo con los otros siete.
2. Las otras aulas sí tienen coincidencias, como MON-ERG-23 en Aula Sur, KEY-MUTE-18 en Aula Este o CAM-ANG-06 en Aula Centro.
3. Cada aula tiene sus propias cuatro tarjetas de micrófono con los mismos nombres.
4. Hay que elegir una instancia por su orden entre ocho casi idénticas, como en el benchmark MRCR.
5. Pide un orden entre bloques, y Aula Norte es el caso con más peso.

**Control, preguntas que no fallan:** la frase de acceso (LUNA-58), el pago duplicado (PAY-8843 por 31,644.80 MXN) y la excepción de costo cero (EXC-4402, de Sonia Méndez) salieron bien también en la conversación muy larga. El deterioro aparece al contar, comparar o elegir entre casi duplicados, no al buscar un dato único.

Pruebas del 17 de octubre de 2026 vía OpenRouter; los resultados varían entre intentos. Con la conversación muy larga, **Claude Sonnet 5.5** acertó las preguntas 1 y 4 y la tarjeta del puesto 16 de Aula Norte: un modelo más grande aleja el deterioro, no lo quita. Cada pregunta manda los 326 mil tokens completos: con Haiku 5.5 cuesta menos de 20 centavos de dólar y con Sonnet 5.5, unos 65.

## Práctica: compactar la conversación larga

### En el chat

1. Primero, con todos los toggles apagados, carga la conversación y haz una de las preguntas: así ves cómo responde el agente con todo el contexto. Después enciende **Compactación** y **Leer y escribir en disco** (el disco hace falta para leer el original archivado) y deja **Todas las tools** apagado para que los schemas no tapen el tamaño de la conversación. Cada toggle abre un chat nuevo.
2. Pulsa **Cargar conversación larga**. Abre un chat nuevo con los 256 mensajes en el historial. Cargarlo no llama a ningún modelo. El botón se puede volver a usar para empezar desde el mismo original.
3. Anota el tamaño del chat en la barra. Inspecciona las instrucciones, tools e historial en la vista de contexto.
4. Pulsa **Compactar sin referencia**. Esta acción hace una llamada a la API. Inspecciona el resumen y el nuevo tamaño del contexto.
5. Pregunta, por ejemplo: **"Según lo acordado en esta conversación, ¿cuál es la ventana de entrega vigente y cuáles se descartaron?"**. Luego pregunta por un detalle: **"Según lo hablado, ¿qué formato y duración de prueba se acordaron en la tarjeta MIC-48K-16?"**. Comprueba primero si ese detalle está en el resumen.
6. Guarda tus observaciones y vuelve a **Cargar conversación larga**, creando otra copia original. Pulsa **Compactar con referencia**.
7. Formula las mismas preguntas. Para un dato omitido en el resumen, pide: **"Lee el historial original usando su referencia y recupera el dato. No lo inventes."**. Observa el segmento naranja cuando se recupera el archivo.

El dataset fuente se mantiene en `datasets/`, **fuera de la carpeta que pueden leer las tools del chat**. Cargarlo no copia ese archivo al workspace. En el modo sin referencia no se crea una copia recuperable del historial; en el modo con referencia se archiva el original dentro de la carpeta del chat. Las respuestas esperadas tampoco están disponibles para el agente.

### Cómo comparar

Usa las 16 preguntas de `preguntas-y-respuestas.json`. Para cada ejecución, registra:

| Pregunta | Resultado (0 / 0.5 / 1) | Fuente de la respuesta | Observación |
|---|---|---|---|
| Identificador de la pregunta | 1: todos los elementos correctos; 0.5: parte correcta sin contradicción; 0: contradice o inventa | Resumen / original recuperado / dato no disponible | Qué omitió o confundió |

Revisa especialmente las correcciones, restricciones y pendientes. Medir cuánto se redujo el contexto no basta si el resumen mantiene una fecha descartada o inventa un abono ya realizado.

La compactación es variable: no se garantiza qué detalle omitirá el modelo. Las dos ejecuciones pueden producir resúmenes diferentes. Conserva los resúmenes y anota cómo obtuvo cada respuesta. Recuperar el archivo completo puede volver a aumentar mucho el contexto; compactar nuevamente permite discutir ese intercambio.

**Prueba real del 12 de octubre de 2026:** con Claude Sonnet 4.6 vía OpenRouter, el contexto activo, con las tools bajo demanda, pasó de 26,250 a 852 tokens estimados después de compactar con referencia. El archivo original conservó los 256 mensajes. El resumen mantuvo los acuerdos principales y varios identificadores; omitió detalles de las pruebas técnicas. Estos resultados corresponden a una ejecución, no a una reducción garantizada. Los dos modos también se verificaron con pruebas controladas, dentro de una suite de 20 pruebas.

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
