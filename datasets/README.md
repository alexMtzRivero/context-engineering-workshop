# Datasets del taller

Dos conversaciones artificiales de soporte entre clientes y un agente de servicio al cliente. Todo es ficticio: las empresas y personas no existen, no se registraron acciones comerciales y los correos usan dominios de ejemplo.

| Archivo | Qué es |
|---|---|
| `conversacion-larga.json` | El caso de Nébula Software: 256 mensajes, listo para cargar |
| `conversacion-larga.md` | El mismo historial en formato de lectura |
| `preguntas-y-respuestas.json` | 16 preguntas con su respuesta esperada para calificar resúmenes; nunca se carga al agente |
| `conversacion-muy-larga.json` | Un análisis de cinco casos casi iguales, Nébula Software entre ellos: 1,282 mensajes |
| `generar_muy_larga.py` | Genera la conversación muy larga a partir de la larga |

## Conversación larga: el caso de Nébula Software

Valeria Ortiz es coordinadora de operaciones de Nébula Software (cuenta CUS-L042) y compró 40 audífonos (pedido ORD-2048) para un taller interno del 19 de octubre de 2026. A lo largo de la conversación resuelve tres frentes con el agente:

- **Equipo incompleto.** Llegaron 36 audífonos: 34 funcionan, 2 están dañados (seriales AO-2048-009 y AO-2048-027) y faltan 4. Se acuerda reponer 6 unidades con el pedido ORD-2053 y la guía SHP-9917. Los dañados se recogen con la etiqueta RET-0726, propuesta para el 20 de octubre de 10:00 a 13:00, a costo cero por la excepción EXC-4402 que autorizó Sonia Méndez. Una cotización de 75 MXN quedó descartada.
- **Entrega.** La ventana vigente es el 18 de octubre de 09:00 a 11:30, en Avenida del Laboratorio 240, edificio B, puerta 3 para proveedores. El día 17 y las 12:30 quedaron descartados. Recibe Paula Ramos; el correo operativo es logistica@nebula.example. Mario León y coordinacion@nebula.example quedaron como antecedentes. La frase de acceso de recepción es LUNA-58. Diego Salas, de logística, debe confirmar antes del 15 de octubre a las 17:00; el caso es SUP-3190 (SUP-3106 queda como antecedente) y la referencia interna de su cola es MESA-27.
- **Cobro duplicado.** PAY-8842 es el pago válido y PAY-8843, por 31,644.80 MXN, el duplicado. La devolución va al medio de pago original, sin crédito ni cupón, con el folio FIN-6631; Laura Peña debe aportar la evidencia. No hay confirmación de abono.

Entre esos acuerdos se intercalan **32 consultas para preparar la sala del taller**, una por puesto (01 a 32). Son cuatro puestos por equipo: audífonos, cámara, router, dock USB, teclado, monitor, micrófono USB y almacenamiento USB. Cada consulta termina en una tarjeta con referencia propia, por ejemplo LAB-BT-04 en el puesto 01. El número de la referencia casi nunca coincide con el del puesto: MIC-48K-16 está en el puesto 27 y la tarjeta del puesto 16 es DOCK-CAB-14. Solo coincide NET-CAN-11. Es una trampa intencional.

Los acuerdos cambian durante la conversación: hay una dirección anterior, otra ventana de entrega, un contacto sustituido y una cotización descartada. Sirve para ver si un resumen conserva el estado vigente y no un dato viejo.

Tamaño: 256 mensajes (128 intercambios) y unos 104 mil caracteres. La página estima unos 26 mil tokens; el proveedor reporta unos 41 mil con Claude 5.5.

## Conversación muy larga: análisis de cinco casos

Una persona de nuestro equipo le pide al agente un análisis de procesos: en las últimas semanas hubo cinco casos casi iguales (pedidos de 40 audífonos con faltantes, dañados, entregas reprogramadas y cobros duplicados) y se sospecha una falla en el proceso. Le pasa las cinco conversaciones completas de soporte, una tras otra, y le pide al final un reporte de qué tienen en común.

Los cinco clientes, en orden:

| # | Cliente | Coordinadora |
|---|---|---|
| 1 | Despacho Ruiz Contadores | Lucía Vega |
| 2 | Clínica Dental Sonrisa | Marta Gil |
| 3 | **Nébula Software** (el caso original) | Valeria Ortiz |
| 4 | Agencia Pixel | Sara Molina |
| 5 | Hotel Mirador | Rosa Medina |

Cada copia cambia el cliente, las seis personas, el dominio del correo, los números de todos los identificadores (ORD-2048 pasa a ORD-2055, ORD-2062...), las fechas, las horas, el monto del cobro duplicado y el número de la dirección. Se conservan las cantidades de equipo y los puestos 01 a 32, así que cada puesto tiene cinco tarjetas casi iguales, una por cliente. Por ejemplo, el puesto 16 tiene DOCK-CAB-21, DOCK-CAB-28, DOCK-CAB-14, DOCK-CAB-35 y DOCK-CAB-42.

Las conversaciones van una tras otra **sin encabezado**: cada una empieza cuando el cliente se presenta. Esos casi duplicados sin separación clara son los que deterioran las respuestas. Tamaño: 1,282 mensajes y unos 520 mil caracteres; la página estima unos 130 mil tokens y el proveedor reporta unos 205 mil.

Se regenera con `python datasets/generar_muy_larga.py`. Acepta el número de clientes (hasta 8) y `--encabezados`, que antepone "Siguiente caso: <cliente>" a cada conversación.

## Preguntas trampa

Con todos los toggles apagados, carga la conversación y haz la pregunta. Estas cinco fallaron con **Claude Haiku 5.5** en la conversación muy larga y salieron bien en la larga:

| # | Pregunta | Respuesta correcta | Conversación larga | Conversación muy larga |
|---|---|---|---|---|
| 1 | En el caso de Nébula Software, ¿cuántas tarjetas tienen una referencia que termina en un número mayor a 20? | 10 | Bien, 3 de 3 | Mal, 3 de 3: "no puedo responder", dice que las tarjetas no son de ningún cliente |
| 2 | En el caso de Nébula Software, lista las tarjetas del micrófono USB con su puesto. | MIC-GAIN-18 (25), MIC-MON-21 (26), MIC-48K-16 (27), MIC-TEST-08 (28) | Bien | Mal, 3 de 3: dice que no están asignadas a Nébula Software o mezcla las de varios clientes |
| 3 | En el caso de Nébula Software, ¿qué tarjetas de la cámara se registraron y en qué puestos? | CAM-1080-30 (05), CAM-ANG-78 (06), CAM-PRIV-03 (07), CAM-UVC-02 (08) | Bien | Mal, 2 de 2: una vez dio solo dos; otra puso CAM-1094-44, de Clínica Dental Sonrisa |
| 4 | En el caso de Nébula Software, ¿cuál fue la última tarjeta que se registró y para qué puesto? | USB-DEV-31, puesto 32 | Bien | Mal, 2 de 2: respondió USB-DEV-59, de Hotel Mirador |
| 5 | En el caso de Nébula Software, ¿qué tarjetas del almacenamiento USB se registraron y en qué puestos? | USB-CAP-512 (29), USB-FMT-17 (30), USB-RESP-23 (31), USB-DEV-31 (32) | Bien | Mal en 1 de 2: dijo que no podía atribuirlas |

Por qué son trampa: las cinco piden todo lo que pertenece a un cliente, y las tarjetas de los cinco clientes tienen los mismos puestos y nombres casi iguales. El modelo deja de saber en qué conversación está cada tarjeta: o se niega, o mezcla las de otro cliente, o toma la última de toda la conversación.

**Control, preguntas que salieron bien en la conversación muy larga:** las tarjetas del router (puestos 09 a 12), la tarjeta del puesto 16, la cuarta tarjeta del puesto 16 en toda la conversación y cuál fue el cuarto caso revisado. Buscar un dato puntual o un cliente por su orden funciona; agrupar todo lo de un cliente, no.

**Los encabezados cambian el resultado.** Con `--encabezados`, Haiku contestó bien el conteo de la pregunta 1, el cruce de números de tarjeta y las preguntas de orden, con cinco clientes y también con ocho (unos 328 mil tokens). Marcar dónde empieza cada caso también es ingeniería de contexto.

**Sonnet 5.5 tampoco sale limpio:** en la pregunta 1 dijo 10, pero su lista incluía tarjetas de otros clientes, como CAM-1094-44.

Pruebas del 17 de octubre de 2026 vía OpenRouter; los resultados varían entre intentos. Cada pregunta manda los 205 mil tokens completos: con Haiku 5.5, que arriba de 100 mil tokens cobra su precio de contexto largo, cuesta unos 10 centavos de dólar; con Sonnet 5.5, unos 41. En unas 40 llamadas con este tamaño, Anthropic rechazó una respuesta con su filtro de contenido; la página lo avisa y basta con volver a preguntar.

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
