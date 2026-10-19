"""80 tools de atención al cliente: catálogo grande, respuestas de texto fijas.

Cada operación tiene nombre, descripción y parámetros propios. Las lecturas responden con texto
sobre los cinco clientes de la conversación muy larga; las escrituras registran una solicitud
simulada y la confirman con un folio, sin cambiar ningún dato.
"""

import re
from typing import Literal

from pydantic import Field, ValidationError, create_model
from pydantic_ai import ModelRetry, RunContext, Tool


# Nombre, propósito y parámetros necesarios. Diez operaciones por área.
OPERATIONS = {
    "clientes": [
        ("get_customer_profile", "Consultar perfil, contacto y nivel del cliente", "customer_id"),
        ("find_customer_by_email", "Encontrar un cliente por su correo electrónico", "email"),
        ("get_customer_addresses", "Consultar las direcciones guardadas del cliente", "customer_id"),
        ("update_customer_address", "Solicitar un cambio de dirección del cliente", "customer_id address"),
        ("get_customer_contact_preferences", "Consultar canales y horarios de contacto preferidos", "customer_id"),
        ("update_customer_contact_preferences", "Solicitar cambiar el canal de contacto preferido", "customer_id channel"),
        ("get_customer_history", "Consultar el historial de atención y compras del cliente", "customer_id"),
        ("get_customer_documents", "Consultar documentos y verificaciones del cliente", "customer_id"),
        ("get_customer_loyalty_points", "Consultar puntos y beneficios de lealtad del cliente", "customer_id"),
        ("update_customer_language", "Solicitar cambiar el idioma de atención del cliente", "customer_id language"),
    ],
    "pedidos": [
        ("get_order_status", "Consultar el estado actual de un pedido", "order_id"),
        ("list_customer_orders", "Consultar los pedidos de un cliente", "customer_id"),
        ("get_order_items", "Consultar productos, cantidades y precios de un pedido", "order_id"),
        ("get_order_timeline", "Consultar los eventos del pedido desde la compra", "order_id"),
        ("get_order_invoice", "Consultar la factura y los datos fiscales del pedido", "order_id"),
        ("cancel_order", "Solicitar cancelar un pedido y registrar el motivo", "order_id reason"),
        ("change_order_address", "Solicitar cambiar la dirección de entrega de un pedido", "order_id address"),
        ("change_order_quantity", "Solicitar cambiar la cantidad de un producto del pedido", "order_id sku quantity"),
        ("add_order_note", "Registrar una nota de atención asociada al pedido", "order_id note"),
        ("request_order_copy", "Solicitar una copia del pedido por un canal de contacto", "order_id channel"),
    ],
    "envios": [
        ("get_shipment_tracking", "Consultar seguimiento y ubicación de un envío", "shipment_id"),
        ("get_order_shipments", "Consultar todos los envíos asociados a un pedido", "order_id"),
        ("get_delivery_estimate", "Consultar la fecha estimada de entrega de un envío", "shipment_id"),
        ("get_delivery_proof", "Consultar la evidencia de entrega y quién recibió", "shipment_id"),
        ("get_carrier_details", "Consultar la transportadora y su canal de atención", "shipment_id"),
        ("get_shipment_events", "Consultar el historial de movimientos y excepciones del envío", "shipment_id"),
        ("reschedule_delivery", "Solicitar una nueva fecha para la entrega del envío", "shipment_id date"),
        ("report_missing_package", "Registrar una solicitud por paquete no recibido", "shipment_id reason"),
        ("report_damaged_package", "Registrar una solicitud por daños en el paquete", "shipment_id reason"),
        ("update_delivery_instructions", "Solicitar nuevas instrucciones para la entrega", "shipment_id note"),
    ],
    "pagos": [
        ("get_payment_status", "Consultar el estado y método de un pago", "payment_id"),
        ("list_order_payments", "Consultar los pagos vinculados a un pedido", "order_id"),
        ("get_payment_receipt", "Consultar el comprobante de un pago", "payment_id"),
        ("get_payment_attempts", "Consultar intentos, rechazos y motivos de fallo de pago", "payment_id"),
        ("get_customer_balance", "Consultar el saldo y movimientos de un cliente", "customer_id"),
        ("get_customer_payment_methods", "Consultar los métodos de pago guardados del cliente", "customer_id"),
        ("request_payment_refund", "Registrar una solicitud de reembolso parcial o total", "payment_id amount reason"),
        ("report_duplicate_charge", "Registrar una solicitud por cobro duplicado", "payment_id reason"),
        ("request_payment_receipt", "Solicitar un comprobante de pago por un canal", "payment_id channel"),
        ("open_payment_dispute", "Registrar una solicitud para investigar un cargo", "payment_id reason"),
    ],
    "devoluciones": [
        ("get_return_status", "Consultar el estado de una devolución", "return_id"),
        ("list_customer_returns", "Consultar las devoluciones de un cliente", "customer_id"),
        ("check_return_eligibility", "Consultar las condiciones de devolución de un pedido", "order_id"),
        ("get_return_policy", "Consultar la política aplicable a un producto", "sku"),
        ("get_return_label", "Consultar la etiqueta de envío de una devolución", "return_id"),
        ("get_return_pickup", "Consultar la recolección programada de una devolución", "return_id"),
        ("get_return_refund_status", "Consultar el reembolso vinculado a una devolución", "return_id"),
        ("request_product_return", "Registrar una solicitud de devolución de producto", "order_id sku reason"),
        ("request_product_exchange", "Registrar una solicitud de cambio de producto", "order_id sku reason"),
        ("cancel_product_return", "Solicitar cancelar una devolución abierta", "return_id reason"),
    ],
    "suscripciones": [
        ("get_subscription_status", "Consultar plan, estado y renovación de una suscripción", "subscription_id"),
        ("list_customer_subscriptions", "Consultar las suscripciones del cliente", "customer_id"),
        ("get_subscription_invoices", "Consultar las facturas de una suscripción", "subscription_id"),
        ("get_subscription_usage", "Consultar consumo y límites de una suscripción", "subscription_id"),
        ("get_subscription_benefits", "Consultar beneficios y servicios incluidos en el plan", "subscription_id"),
        ("get_subscription_renewal", "Consultar la próxima fecha y costo de renovación", "subscription_id"),
        ("change_subscription_plan", "Solicitar cambiar el plan de una suscripción", "subscription_id plan"),
        ("pause_subscription", "Solicitar pausar una suscripción con motivo", "subscription_id reason"),
        ("resume_subscription", "Solicitar reactivar una suscripción pausada", "subscription_id"),
        ("cancel_subscription", "Solicitar cancelar una suscripción y registrar el motivo", "subscription_id reason"),
    ],
    "soporte": [
        ("get_support_ticket", "Consultar el estado y conversación de un ticket", "ticket_id"),
        ("list_customer_tickets", "Consultar los tickets del cliente", "customer_id"),
        ("get_ticket_messages", "Consultar los mensajes e historial de un ticket", "ticket_id"),
        ("get_ticket_sla", "Consultar el plazo y prioridad de atención de un ticket", "ticket_id"),
        ("get_ticket_assignment", "Consultar el equipo y agente asignados al ticket", "ticket_id"),
        ("create_support_ticket", "Registrar una solicitud para abrir un ticket de soporte", "customer_id subject priority"),
        ("add_ticket_message", "Registrar una solicitud para añadir un mensaje al ticket", "ticket_id note"),
        ("escalate_support_ticket", "Solicitar escalar un ticket a un equipo especializado", "ticket_id reason"),
        ("close_support_ticket", "Solicitar cerrar un ticket con una nota de resolución", "ticket_id note"),
        ("request_human_agent", "Solicitar atención de una persona por el canal elegido", "customer_id channel reason"),
    ],
    "productos": [
        ("get_product_details", "Consultar descripción y especificaciones de un producto", "sku"),
        ("search_product_catalog", "Buscar productos por nombre o palabra clave", "query"),
        ("get_product_stock", "Consultar existencias y disponibilidad de un producto", "sku"),
        ("get_product_price", "Consultar precio, moneda y descuentos vigentes", "sku"),
        ("get_product_warranty", "Consultar cobertura y condiciones de garantía", "sku"),
        ("get_product_manual", "Consultar manual y recomendaciones de uso del producto", "sku"),
        ("get_product_compatibility", "Consultar compatibilidad con accesorios y equipos", "sku"),
        ("get_product_alternatives", "Consultar alternativas a un producto agotado", "sku"),
        ("get_product_reviews", "Consultar valoraciones y comentarios del producto", "sku"),
        ("request_stock_notification", "Solicitar un aviso cuando el producto esté disponible", "customer_id sku channel"),
    ],
}

# Los schemas repiten campos reales de una API: esa repetición ocupa contexto.
PARAMETERS = {
    "customer_id": (str, Field(..., min_length=1, description="Identificador del cliente confirmado en el sistema. Por ejemplo CUS-L042, de Nébula Software; no deduzcas el ID a partir del nombre.")),
    "order_id": (str, Field(..., min_length=1, description="Identificador del pedido que el cliente desea consultar o gestionar, por ejemplo ORD-2048. No es el ID del envío ni del pago.")),
    "shipment_id": (str, Field(..., min_length=1, description="Identificador del envío o guía, por ejemplo SHP-9917. Un pedido puede tener varios envíos; usa la guía correspondiente.")),
    "payment_id": (str, Field(..., min_length=1, description="Identificador de la transacción de pago, por ejemplo PAY-8843. No envíes números completos de tarjetas ni credenciales.")),
    "return_id": (str, Field(..., min_length=1, description="Identificador de la devolución previamente registrada, por ejemplo RET-0726; distinto al identificador del pedido original.")),
    "subscription_id": (str, Field(..., min_length=1, description="Identificador de la suscripción que se consulta o modifica, por ejemplo SUB-001. Permite distinguir varias suscripciones del cliente.")),
    "ticket_id": (str, Field(..., min_length=1, description="Identificador del ticket de soporte, por ejemplo SUP-3190. Usa un ticket existente para consultar o registrar solicitudes asociadas.")),
    "sku": (str, Field(..., min_length=1, description="Código del producto dentro del catálogo, por ejemplo SKU-AUD-01. Identifica una variante concreta y evita confundirla con el pedido.")),
    "email": (str, Field(..., min_length=3, description="Correo informado por el cliente para localizar su cuenta. Por ejemplo logistica@nebula.example.")),
    "address": (str, Field(..., min_length=1, description="Dirección completa solicitada: calle, número, ciudad y código postal. Se registra como solicitud; no se cambia una entrega real.")),
    "reason": (str, Field(..., min_length=1, description="Motivo descrito por el cliente. Conserva el contexto necesario para que una persona pueda revisar la solicitud sin inventar hechos.")),
    "note": (str, Field(..., min_length=1, description="Texto de la nota o mensaje que se desea registrar. Debe describir el acuerdo con el cliente y los próximos pasos de atención.")),
    "subject": (str, Field(..., min_length=1, description="Asunto breve del problema para identificar la solicitud de soporte, por ejemplo paquete no recibido o cobro que no reconozco.")),
    "channel": (Literal["email", "chat", "telefono"], Field(..., description="Canal de contacto pedido por el cliente: email, chat o telefono. Esta demo no envía mensajes ni realiza llamadas externas.")),
    "language": (Literal["es", "en", "pt"], Field(..., description="Idioma preferido para las siguientes interacciones: español, inglés o portugués. Registra la preferencia solicitada por el cliente.")),
    "quantity": (int, Field(..., ge=1, le=100, description="Cantidad de unidades solicitada para el producto indicado. Debe ser un entero positivo; el cambio se registra para revisión.")),
    "amount": (float, Field(..., gt=0, description="Importe solicitado para el reembolso, expresado en la moneda del pago. No implica autorización financiera ni mueve dinero real.")),
    "date": (str, Field(..., min_length=10, description="Fecha solicitada con formato AAAA-MM-DD. La disponibilidad de una entrega real debe revisarse antes de confirmar un cambio.")),
    "priority": (Literal["baja", "normal", "alta", "urgente"], Field(..., description="Prioridad de atención según el impacto que describe el cliente. Utiliza urgente solo cuando el problema requiere atención inmediata.")),
    "plan": (Literal["basic", "pro", "enterprise"], Field(..., description="Nombre del plan solicitado: basic, pro o enterprise. Se registra la solicitud de cambio; no se generan cargos ni compromisos reales.")),
    "query": (str, Field(..., min_length=1, description="Palabra o frase para buscar en los productos disponibles, por ejemplo audífonos. La búsqueda usa el catálogo ficticio del taller.")),
}
OPTIONS = {
    "include_history": (bool, Field(False, description="Incluye antecedentes disponibles en la respuesta. Actívalo si necesitas entender eventos previos, no para una consulta simple de estado.")),
    "detail_level": (Literal["resumen", "completo"], Field("resumen", description="Nivel de detalle solicitado para interpretar la operación. resumen prioriza lo esencial; completo solicita la información disponible.")),
    "locale": (Literal["es-MX", "es-CO", "en-US"], Field("es-MX", description="Región e idioma para presentar fechas, importes y etiquetas al cliente. No cambia la moneda original de una transacción.")),
}


# Las lecturas se reconocen por el prefijo del nombre; el resto registra solicitudes simuladas.
READ_TOOL_NAMES = {
    name for rows in OPERATIONS.values() for name, _, _ in rows
    if name.startswith(("get_", "list_", "find_", "search_", "check_"))
}
CUSTOMER_CATALOG = {
    name: f"{area}: {purpose}. " + (
        "Devuelve datos ficticios de esta área para responder al cliente con información del sistema. "
        "Usa los identificadores confirmados; si no encuentra coincidencias, informa que faltan datos."
        if name in READ_TOOL_NAMES else
        "Registra una solicitud simulada en la sesión para revisión. Devuelve su folio y estado registrado; "
        "no confirma que el cambio comercial ya se haya aplicado ni ejecuta acciones externas."
    )
    for area, rows in OPERATIONS.items() for name, purpose, _ in rows
}


# Los cinco clientes de datasets/conversacion-muy-larga/. k desplaza los identificadores, las
# fechas y las horas igual que en la conversación: ORD-2048 de Nébula es ORD-2055 en Despacho Ruiz.
CLIENTES = [
    (0, "Nébula Software", "nebula.example",
     ["Valeria Ortiz", "Paula Ramos", "Diego Salas", "Mario León", "Sonia Méndez", "Laura Peña"]),
    (1, "Despacho Ruiz Contadores", "ruizcontadores.example",
     ["Lucía Vega", "Andrea Soto", "Tomás Ruiz", "Iván Mora", "Elena Cruz", "Rocío Lara"]),
    (2, "Clínica Dental Sonrisa", "sonrisa.example",
     ["Marta Gil", "Carla Ríos", "Pablo Nieto", "Raúl Vidal", "Inés Prado", "Noelia Paz"]),
    (3, "Agencia Pixel", "agenciapixel.example",
     ["Sara Molina", "Julia Campos", "Hugo Serra", "Óscar Rey", "Alba Nuñez", "Clara Ibáñez"]),
    (4, "Hotel Mirador", "hotelmirador.example",
     ["Rosa Medina", "Irene Pastor", "Bruno Lago", "Félix Ortega", "Lidia Marín", "Gloria Fuentes"]),
]
SKU = "SKU-AUD-01"


def desplazar(identificador: str, k: int) -> str:
    # Suma 7 por cliente a cada grupo de dígitos, conservando su largo.
    return re.sub(r"\d+", lambda m: str((int(m.group()) + 7 * k) % 10 ** len(m.group())).zfill(len(m.group())), identificador)


def cliente(k: int, empresa: str, dominio: str, personas: list[str]) -> dict:
    coordinadora, recibe, logistica, contacto_anterior, autoriza, finanzas = personas
    precio = 899 + 10 * k
    ident = lambda base: desplazar(base, k)
    hora = lambda h: f"{(h + (k % 3 + 1 if k else 0)) % 24:02d}"
    return {
        "empresa": empresa, "coordinadora": coordinadora, "recibe": recibe, "logistica": logistica,
        "contacto_anterior": contacto_anterior, "autoriza": autoriza, "finanzas": finanzas,
        "cuenta": ident("CUS-L042"), "correo": f"logistica@{dominio}", "correo_anterior": f"coordinacion@{dominio}",
        "pedido": ident("ORD-2048"), "reposicion": ident("ORD-2053"), "guia": ident("SHP-9917"), "frase": ident("LUNA-58"),
        "pago": ident("PAY-8842"), "duplicado": ident("PAY-8843"), "folio_fin": ident("FIN-6631"),
        "devolucion": ident("RET-0726"), "excepcion": ident("EXC-4402"),
        "caso": ident("SUP-3190"), "caso_anterior": ident("SUP-3106"), "cola": ident("MESA-27"),
        "codigo": ident("TALLER-12"), "danados": f"{ident('AO-2048-009')} y {ident('AO-2048-027')}",
        "precio": f"{precio} MXN", "subtotal": f"{40 * precio:,} MXN",
        "descuento": f"{4.8 * precio:,.2f} MXN", "total": f"{35.2 * precio:,.2f} MXN",
        "direccion": f"Avenida del Laboratorio {240 + 13 * k}, edificio B, puerta 3 para proveedores",
        "taller": f"{19 + k} de octubre de 2026",
        "entrega": f"{18 + k} de octubre de 2026, de {hora(9)}:00 a {hora(11)}:30",
        "recogida": f"{20 + k} de octubre de 2026, de {hora(10)}:00 a {hora(13)}:00",
        "plazo": f"{15 + k} de octubre de 2026 a las {hora(17)}:00",
    }


REGISTROS = [cliente(*datos) for datos in CLIENTES]
# Qué identificador encuentra a qué cliente, y de qué tipo es: un pedido puede ser el original o la reposición.
INDICE = {}
for r in REGISTROS:
    for campo, valor, tipo in [
        ("customer_id", r["cuenta"], "*"), ("email", r["correo"], "vigente"), ("email", r["correo_anterior"], "anterior"),
        ("order_id", r["pedido"], "pedido"), ("order_id", r["reposicion"], "reposicion"), ("shipment_id", r["guia"], "*"),
        ("payment_id", r["pago"], "valido"), ("payment_id", r["duplicado"], "duplicado"), ("return_id", r["devolucion"], "*"),
        ("ticket_id", r["caso"], "caso"), ("ticket_id", r["caso_anterior"], "antecedente"), ("ticket_id", r["cola"], "cola"),
    ]:
        INDICE[(campo, valor.casefold())] = (r, tipo)

# Respuesta de cada lectura. Un dict elige el texto según el tipo de identificador; "*" sirve para todos.
LECTURAS = {
    "get_customer_profile": "{empresa}, cuenta {cuenta}. Contacto principal: {coordinadora}, coordinadora de operaciones. Correo operativo: {correo}. Tiene el pedido {pedido} y el caso de soporte {caso} abiertos.",
    "find_customer_by_email": {
        "vigente": "{valor} es el correo operativo de {empresa} (cuenta {cuenta}), contacto {coordinadora}.",
        "anterior": "{valor} era el correo de {empresa} (cuenta {cuenta}); quedó como antecedente. El correo operativo vigente es {correo}.",
    },
    "get_customer_addresses": "Dirección de entrega vigente de {empresa}: {direccion}. La propuesta anterior, Calle del Taller 18, puerta principal, quedó descartada.",
    "get_customer_contact_preferences": "{empresa} recibe los avisos solo por correo, en {correo}; no autoriza llamadas ni WhatsApp. Quien recibe las entregas es {recibe}; {contacto_anterior} ya no es el contacto de entrega.",
    "get_customer_history": "Historial de {empresa}: compró 40 audífonos en el pedido {pedido} para su taller del {taller}; abrió el caso {caso} por 4 faltantes y 2 dañados (antecedente {caso_anterior}); se creó la reposición {reposicion}, la devolución {devolucion} y la revisión de cobro duplicado {folio_fin}.",
    "get_customer_documents": "La cuenta {cuenta} de {empresa} está verificada. En sus casos consta la autorización de recogida sin costo {excepcion}. No hay comprobante de abono del reembolso de {duplicado}.",
    "get_customer_loyalty_points": "{empresa} es una cuenta empresarial y no participa en el programa de puntos.",
    "get_order_status": {
        "pedido": "Pedido {pedido} de {empresa}: entregado incompleto. Llegaron 36 de 40 audífonos: 34 funcionan, 2 están dañados ({danados}) y faltan 4. La reposición de 6 unidades va en el pedido {reposicion}.",
        "reposicion": "Pedido {reposicion} de {empresa}: reposición sin costo de 6 audífonos (4 faltantes y 2 dañados de {pedido}). Viaja con la guía {guia}; la entrega acordada es el {entrega} y la transportadora aún no la confirma.",
    },
    "list_customer_orders": "{empresa} tiene dos pedidos: {pedido}, de 40 audífonos por {total}, y {reposicion}, de 6 audífonos de reposición sin costo.",
    "get_order_items": {
        "pedido": "{pedido}: 40 audífonos {sku} a {precio} cada uno. Subtotal {subtotal}; descuento {codigo} del 12 %, {descuento}; total {total}. Envío sin costo.",
        "reposicion": "{reposicion}: 6 audífonos {sku} sin costo, como reposición del pedido {pedido}.",
    },
    "get_order_timeline": {
        "pedido": "{pedido}: compra pagada con {pago}; después apareció un segundo cargo, {duplicado}; la entrega llegó incompleta (36 de 40); se abrió el caso {caso} y se creó la reposición {reposicion}.",
        "reposicion": "{reposicion}: creado como reposición de {pedido}; guía {guia} generada; entrega acordada para el {entrega}; todavía sin entrega confirmada.",
    },
    "get_order_invoice": {
        "pedido": "Factura del pedido {pedido} a nombre de {empresa}: subtotal {subtotal}, descuento {codigo} por {descuento}, total {total}. Pagada con {pago}.",
        "reposicion": "{reposicion} no genera factura: es una reposición sin costo del pedido {pedido}.",
    },
    "get_shipment_tracking": "Guía {guia} (reposición {reposicion} de {empresa}): lista para la entrega del {entrega} en {direccion}. Falta que la transportadora confirme la ventana.",
    "get_order_shipments": {
        "pedido": "{pedido} tuvo un envío original que llegó incompleto (36 de 40 audífonos). La reposición {reposicion} viaja con la guía {guia}.",
        "reposicion": "{reposicion} viaja con la guía {guia}, con entrega acordada el {entrega}.",
    },
    "get_delivery_estimate": "Entrega estimada de la guía {guia}: {entrega}. Es la ventana acordada con {empresa}; la transportadora aún no la confirma.",
    "get_delivery_proof": "La guía {guia} todavía no tiene evidencia de entrega. Debe recibirla {recibe} con la frase de acceso {frase}.",
    "get_carrier_details": "La guía {guia} va con la transportadora asignada por logística. {logistica} debe confirmar la ventana antes del {plazo}; si no, se escala.",
    "get_shipment_events": "Guía {guia}: creada para la reposición {reposicion}; una propuesta anterior de fecha y dirección quedó descartada; ventana vigente {entrega}. Aún no hay movimientos de entrega.",
    "get_payment_status": {
        "valido": "{pago} de {empresa}: pago válido por {total} del pedido {pedido}. Se mantiene.",
        "duplicado": "{duplicado} de {empresa}: segundo cargo por {total} del pedido {pedido}. Está en revisión con el folio {folio_fin}; la devolución va al medio de pago original y todavía no hay confirmación de abono.",
    },
    "list_order_payments": {
        "pedido": "{pedido} tiene dos cargos por {total}: {pago}, válido, y {duplicado}, duplicado y en revisión con el folio {folio_fin}.",
        "reposicion": "{reposicion} no tiene pagos: es una reposición sin costo.",
    },
    "get_payment_receipt": {
        "valido": "Comprobante de {pago}: {total} por el pedido {pedido} de {empresa}.",
        "duplicado": "Comprobante de {duplicado}: {total}, segundo cargo del pedido {pedido} de {empresa}. En revisión con el folio {folio_fin}.",
    },
    "get_payment_attempts": "{pago} se aprobó al primer intento. {duplicado} se registró después por el mismo importe y no corresponde a otro pedido.",
    "get_customer_balance": "{empresa} no tiene saldo a favor: pidió que el cargo duplicado {duplicado}, de {total}, se devuelva al medio de pago original y no como crédito. La devolución está en revisión con el folio {folio_fin}.",
    "get_customer_payment_methods": "{empresa} pagó con el medio corporativo registrado en {pago}. Las devoluciones se hacen a ese mismo medio.",
    "get_return_status": "Devolución {devolucion} de {empresa}: recogida de los 2 audífonos dañados ({danados}), propuesta para el {recogida}. Sin costo por la excepción {excepcion}, que autorizó {autoriza}. Falta confirmarla.",
    "list_customer_returns": "{empresa} tiene una devolución: {devolucion}, de los 2 audífonos dañados del pedido {pedido}.",
    "check_return_eligibility": {
        "pedido": "Los 2 audífonos dañados de {pedido} se pueden devolver sin costo con la excepción {excepcion}. Los 34 que funcionan se quedan con {empresa}.",
        "reposicion": "{reposicion} todavía no se entrega, así que no tiene devoluciones.",
    },
    "get_return_label": "La etiqueta de {devolucion} va en la caja de los 2 audífonos dañados ({danados}) y se usa en la recogida del {recogida}.",
    "get_return_pickup": "Recogida de {devolucion}: {recogida}, en {direccion}, después de recibir la reposición. Falta confirmarla.",
    "get_return_refund_status": "{devolucion} no genera reembolso: los dañados se reponen con {reposicion}. El reembolso abierto es el del cargo duplicado {duplicado}, folio {folio_fin}.",
    "list_customer_subscriptions": "{empresa} no tiene suscripciones activas.",
    "get_support_ticket": {
        "caso": "{caso} de {empresa}: caso maestro abierto por 4 faltantes y 2 dañados del pedido {pedido}. Responsable de logística: {logistica}. {caso_anterior} queda como antecedente.",
        "antecedente": "{caso_anterior} es un antecedente de {empresa}; la atención sigue en el caso maestro {caso}.",
        "cola": "{cola} es la referencia interna de la cola de logística de {empresa}, ligada al caso {caso}. No es una mesa física ni una dirección.",
    },
    "list_customer_tickets": "{empresa} tiene abierto el caso maestro {caso}; {caso_anterior} quedó como antecedente.",
    "get_ticket_messages": "Últimos mensajes del caso {caso}: {coordinadora} pidió reponer 6 audífonos sin cancelar el pedido; se acordó la entrega del {entrega} con {recibe}; {logistica} debe confirmar la ventana antes del {plazo}.",
    "get_ticket_sla": "Caso {caso}: prioridad alta por el taller del {taller}. {logistica} debe confirmar antes del {plazo}; si no, se escala.",
    "get_ticket_assignment": "El caso {caso} está asignado a logística, con {logistica} como responsable. El folio financiero {folio_fin} depende de que {finanzas} aporte la evidencia del resultado.",
}
PRODUCTO = {
    "get_product_details": "{sku}: audífonos inalámbricos para videollamadas. Bluetooth; se emparejan con un equipo a la vez y recuerdan hasta dos. Batería de 28 horas a volumen medio. Micrófono integrado para videollamadas, no para grabación.",
    "get_product_stock": "{sku}: 120 unidades disponibles para entrega inmediata.",
    "get_product_price": "{sku}: precio de lista 899 MXN. Cada pedido conserva el precio con el que se facturó.",
    "get_product_warranty": "{sku}: 12 meses de garantía contra defectos de fabricación. Los daños de envío se atienden con reposición, no con garantía.",
    "get_product_manual": "{sku}: cargar dos horas antes del primer uso. Limpiar las almohadillas con un paño ligeramente húmedo, sin sumergir el equipo ni usar disolventes. Para cambiar de equipo, olvidar el dispositivo anterior y volver a emparejar.",
    "get_product_compatibility": "{sku} funciona por Bluetooth con computadoras y teléfonos. Recuerda hasta dos dispositivos, pero no reproduce audio en dos equipos al mismo tiempo.",
    "get_product_alternatives": "{sku} tiene existencias, así que no hace falta una alternativa.",
    "get_product_reviews": "{sku}: 4.6 de 5 en 212 opiniones. Lo más valorado es la batería; lo más criticado, que no se conecta a dos equipos al mismo tiempo.",
    "get_return_policy": "{sku}: devolución dentro de 30 días si llega dañado o incompleto. La recogida cuesta 75 MXN, salvo que se autorice una excepción sin costo.",
}
ESCRITURAS = {
    "update_customer_address": "cambio de dirección", "update_customer_contact_preferences": "cambio de canal de contacto",
    "update_customer_language": "cambio de idioma de atención", "cancel_order": "cancelación del pedido",
    "change_order_address": "cambio de dirección de entrega", "change_order_quantity": "cambio de cantidad",
    "add_order_note": "nota en el pedido", "request_order_copy": "copia del pedido",
    "reschedule_delivery": "nueva fecha de entrega", "report_missing_package": "reporte de paquete no recibido",
    "report_damaged_package": "reporte de paquete dañado", "update_delivery_instructions": "nuevas instrucciones de entrega",
    "request_payment_refund": "reembolso", "report_duplicate_charge": "revisión de cobro duplicado",
    "request_payment_receipt": "comprobante de pago", "open_payment_dispute": "investigación del cargo",
    "request_product_return": "devolución de producto", "request_product_exchange": "cambio de producto",
    "cancel_product_return": "cancelación de la devolución", "change_subscription_plan": "cambio de plan",
    "pause_subscription": "pausa de la suscripción", "resume_subscription": "reactivación de la suscripción",
    "cancel_subscription": "cancelación de la suscripción", "create_support_ticket": "nuevo ticket de soporte",
    "add_ticket_message": "mensaje en el ticket", "escalate_support_ticket": "escalamiento del ticket",
    "close_support_ticket": "cierre del ticket", "request_human_agent": "atención de una persona",
    "request_stock_notification": "aviso de disponibilidad",
}
ETIQUETAS = {"reason": "motivo", "address": "dirección", "note": "nota", "channel": "canal", "date": "fecha", "amount": "importe",
             "quantity": "cantidad", "sku": "producto", "plan": "plan", "subject": "asunto", "priority": "prioridad", "language": "idioma"}


def lectura(name: str, campo: str, valor: str) -> str:
    """El texto fijo que regresa una lectura para un identificador."""
    if campo in ("sku", "query"):
        if campo == "query":
            encontrado = any(palabra in valor.casefold() for palabra in ("audíf", "audif", "auricular", "bluetooth", "diadema"))
            return (f"Encontré 1 producto: {SKU}, audífonos inalámbricos para videollamadas, 899 MXN de lista."
                    if encontrado else f"No hay productos que coincidan con «{valor}».")
        return PRODUCTO[name].format(sku=SKU) if valor.casefold() == SKU.casefold() else f"No encontré el producto {valor}."
    if (campo, valor.casefold()) not in INDICE:
        return f"No encontré {valor}. Revisa el identificador con el cliente."
    registro, tipo = INDICE[(campo, valor.casefold())]
    plantilla = LECTURAS.get(name, "No hay información de {valor}.")
    if isinstance(plantilla, dict):
        plantilla = plantilla.get(tipo) or next(iter(plantilla.values()))
    return plantilla.format(**registro, valor=valor, sku=SKU)


def make_tool(area: str, name: str, fields: str) -> Tool:
    # Pydantic genera un schema distinto por operación y valida los argumentos.
    arguments = create_model(name + "_arguments", **{key: PARAMETERS[key] for key in fields.split()}, **OPTIONS)
    campo = fields.split()[0]

    def run(ctx: RunContext, **kwargs) -> str:
        try:
            request = arguments.model_validate(kwargs).model_dump()
        except ValidationError as error:
            raise ModelRetry(str(error)) from error
        valor = str(request[campo])
        # Lectura: un texto fijo con los datos del cliente que corresponde al identificador.
        if name in READ_TOOL_NAMES:
            return lectura(name, campo, valor)
        # Escritura: no cambia datos, solo registra la solicitud con un folio.
        encontrado = INDICE.get((campo, valor.casefold()))
        if campo != "sku" and not encontrado:
            return f"No encontré {valor}; no se registró ninguna solicitud."
        entry = {"simulated": True, "operation": name, "request_id": f"REQ-{len(ctx.deps.service_requests) + 1:03}", "status": "solicitud registrada", "arguments": request}
        ctx.deps.service_requests.append(entry)
        detalle = "; ".join(f"{ETIQUETAS[key]} «{request[key]}»" for key in fields.split()[1:] if key in ETIQUETAS)
        empresa = f" ({encontrado[0]['empresa']})" if encontrado else ""
        return (f"Solicitud {entry['request_id']} registrada: {ESCRITURAS[name]} para {valor}{empresa}."
                + (f" Detalle: {detalle}." if detalle else "") + " Queda pendiente de revisión; no se aplicó ningún cambio.")

    # El mismo handler sirve a las 80 tools; lo que cambia entre ellas es el schema que ve el modelo.
    return Tool.from_schema(run, name=name, description=CUSTOMER_CATALOG[name], json_schema=arguments.model_json_schema(), takes_ctx=True, sequential=True)


CUSTOMER_TOOLS = [make_tool(area, name, fields) for area, rows in OPERATIONS.items() for name, _, fields in rows]
