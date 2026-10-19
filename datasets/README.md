# Conversación muy larga

La conversación está en `conversacion-muy-larga/`, partida en archivos: `00-introduccion.json` (el pedido del análisis) y uno por cliente, en el orden en que aparecen. Juntos, en orden, son los 1,282 mensajes; cada archivo de cliente sirve también por separado para el agente de ese cliente (paso 5).

Una persona del equipo le pide al agente analizar cinco casos de soporte casi iguales para encontrar por qué se repiten. Le pasa las cinco conversaciones completas, una tras otra: Despacho Ruiz Contadores, Clínica Dental Sonrisa, Nébula Software, Agencia Pixel y Hotel Mirador. En cada una, el cliente reporta audífonos faltantes y dañados y un cobro duplicado y, entre los mensajes del pedido, prepara la sala de su taller: para cada uno de 32 puestos pide una prueba del equipo, que el agente registra como una tarjeta con identificador (por ejemplo, LAB-BT-04). Todo es ficticio.

## Preguntas trampa

| Pregunta | Respuesta correcta |
|---|---|
| ¿Cuál de los cinco clientes recibe su reposición primero? | Nébula Software, el 18 de octubre de 2026 de 09:00 a 11:30 |
| ¿A qué dirección se entrega el pedido de cada cliente? | Cada uno a la suya, en Avenida del Laboratorio, edificio B, puerta 3: Despacho Ruiz Contadores 253, Clínica Dental Sonrisa 266, Nébula Software 240, Agencia Pixel 279 y Hotel Mirador 292 |
| ¿Qué tan avanzada está la preparación de la sala de cada cliente? | Igual en los cinco: 32 tarjetas cada uno y ninguna prueba ejecutada |
| ¿Cómo va la preparación de la sala de Nébula Software? | Tiene sus 32 tarjetas registradas, una por puesto, todas con el procedimiento definido y la prueba pendiente |
| ¿Cuántas tarjetas de preparación registró cada cliente? | 32 cada uno, 160 en total |
| ¿Qué equipos tiene que probar cada cliente antes de su taller? | Los mismos ocho en los cinco: audífonos, cámara, router, dock USB, teclado, monitor, micrófono USB y almacenamiento USB, en cuatro puestos cada uno |

La de la demo es la de la reposición (respuesta rápida 1 de la página). Con Haiku 5.5, el prompt de analista, todo apagado y un chat nuevo por intento, falló 10 de 13 veces el 19 de octubre de 2026: suele decir que no hay un orden de prioridad entre los clientes. Después de compactar con referencia la resolvió 4 de 4: el resumen no trae las fechas, pero el agente las encuentra con `search_file` (de 20 a 66 mil tokens de entrada). Las preguntas de un solo dato de Nébula (seriales, folio, frase de acceso) y las de comparar clientes las acierta aun con todo apagado. La de la sala de cada cliente también falla, pero es ambigua: la conversación llama a las tarjetas «planificación del laboratorio» y nunca dice de qué cliente es cada sala. Si el filtro de contenido del proveedor bloquea una respuesta, el servidor reintenta hasta dos veces.
