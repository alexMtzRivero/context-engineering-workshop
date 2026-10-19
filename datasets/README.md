# Conversación muy larga

Una persona del equipo le pide al agente analizar cinco casos de soporte casi iguales para encontrar por qué se repiten. Le pasa las cinco conversaciones completas, una tras otra: Despacho Ruiz Contadores, Clínica Dental Sonrisa, Nébula Software, Agencia Pixel y Hotel Mirador. En cada una, el cliente reporta audífonos faltantes y dañados y un cobro duplicado y, entre los mensajes del pedido, prepara la sala de su taller: para cada uno de 32 puestos pide una prueba del equipo, que el agente registra como una tarjeta con identificador (por ejemplo, LAB-BT-04). Todo es ficticio.

## Preguntas trampa

| Pregunta | Respuesta correcta |
|---|---|
| ¿A qué dirección se entrega el pedido de cada cliente? | Cada uno a la suya, en Avenida del Laboratorio, edificio B, puerta 3: Despacho Ruiz Contadores 253, Clínica Dental Sonrisa 266, Nébula Software 240, Agencia Pixel 279 y Hotel Mirador 292 |
| ¿Qué tan avanzada está la preparación de la sala de cada cliente? | Igual en los cinco: 32 tarjetas cada uno y ninguna prueba ejecutada |
| ¿Cómo va la preparación de la sala de Nébula Software? | Tiene sus 32 tarjetas registradas, una por puesto, todas con el procedimiento definido y la prueba pendiente |
| ¿Cuántas tarjetas de preparación registró cada cliente? | 32 cada uno, 160 en total |
| ¿Qué equipos tiene que probar cada cliente antes de su taller? | Los mismos ocho en los cinco: audífonos, cámara, router, dock USB, teclado, monitor, micrófono USB y almacenamiento USB, en cuatro puestos cada uno |

La más confiable para la demo es la de la sala de cada cliente (respuesta rápida 1 de la página). Con Haiku 5.5, todo apagado y un chat nuevo por intento, falló 4 de 4 veces el 18 de octubre de 2026 y otras 4 de 4 el 19, ya con el prompt de analista. Responde con seguridad que las tarjetas no son de ningún cliente o le asigna a todos las de Hotel Mirador: si no separa los puestos por cliente ni menciona 160 tarjetas, falló. La de Nébula Software falla seguido, pero a veces acierta. Si el proveedor responde con el aviso de su filtro de contenido, basta con volver a preguntar.
