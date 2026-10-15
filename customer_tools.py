"""80 tools de atención al cliente: catálogo grande, implementación simulada pequeña.

Cada operación tiene nombre, descripción y parámetros propios. Las lecturas usan
datos ficticios; las escrituras registran solicitudes dentro de la sesión.
"""

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
    "customer_id": (str, Field(..., min_length=1, description="Identificador del cliente confirmado en el sistema. En esta demo usa CUS-001; no deduzcas el ID a partir del nombre.")),
    "order_id": (str, Field(..., min_length=1, description="Identificador del pedido que el cliente desea consultar o gestionar, por ejemplo ORD-1001. No es el ID del envío ni del pago.")),
    "shipment_id": (str, Field(..., min_length=1, description="Identificador del envío o guía, por ejemplo SHP-001. Un pedido puede tener varios envíos; usa la guía correspondiente.")),
    "payment_id": (str, Field(..., min_length=1, description="Identificador de la transacción de pago, por ejemplo PAY-001. No envíes números completos de tarjetas ni credenciales.")),
    "return_id": (str, Field(..., min_length=1, description="Identificador de la devolución previamente registrada, por ejemplo RET-001; distinto al identificador del pedido original.")),
    "subscription_id": (str, Field(..., min_length=1, description="Identificador de la suscripción que se consulta o modifica, por ejemplo SUB-001. Permite distinguir varias suscripciones del cliente.")),
    "ticket_id": (str, Field(..., min_length=1, description="Identificador del ticket de soporte, por ejemplo TKT-001. Usa un ticket existente para consultar o registrar solicitudes asociadas.")),
    "sku": (str, Field(..., min_length=1, description="Código del producto dentro del catálogo, por ejemplo SKU-001. Identifica una variante concreta y evita confundirla con el pedido.")),
    "email": (str, Field(..., min_length=3, description="Correo informado por el cliente para localizar su cuenta. En los datos ficticios de este taller existe ana@example.com.")),
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


DATA = {
    "clientes": [{"customer_id": "CUS-001", "name": "Ana García", "email": "ana@example.com", "language": "es", "channel": "email", "address": "Calle Ejemplo 123, Ciudad Demo", "loyalty_points": 1250, "documents": ["Cuenta verificada"], "history": ["Compra ORD-1001", "Ticket TKT-001"]}],
    "pedidos": [{"order_id": "ORD-1001", "customer_id": "CUS-001", "status": "en tránsito", "total": 1499, "currency": "MXN", "items": [{"sku": "SKU-001", "quantity": 1}], "invoice": "INV-001", "timeline": ["Compra confirmada", "Paquete enviado"], "shipment_id": "SHP-001"}],
    "envios": [{"shipment_id": "SHP-001", "order_id": "ORD-1001", "carrier": "Paquetería Demo", "status": "en tránsito", "delivery_estimate": "2026-10-19", "events": ["Recolectado", "En centro de distribución"], "delivery_proof": None}],
    "pagos": [{"payment_id": "PAY-001", "order_id": "ORD-1001", "customer_id": "CUS-001", "status": "aprobado", "amount": 1499, "currency": "MXN", "method": "Tarjeta demo terminación 4242", "receipt": "REC-001", "balance": 0, "attempts": ["Aprobado en el primer intento"]}],
    "devoluciones": [{"return_id": "RET-001", "order_id": "ORD-1001", "customer_id": "CUS-001", "sku": "SKU-001", "status": "solicitud en revisión", "policy": "30 días, producto sin daños", "eligible": True, "label": "LABEL-DEMO-001", "pickup": "pendiente", "refund_status": "pendiente de revisión"}],
    "suscripciones": [{"subscription_id": "SUB-001", "customer_id": "CUS-001", "plan": "pro", "status": "activa", "renewal": "2026-11-01", "price": 299, "currency": "MXN", "usage": "3 de 10 beneficios utilizados", "benefits": ["Envíos incluidos", "Soporte preferente"], "invoices": ["INV-SUB-001"]}],
    "soporte": [{"ticket_id": "TKT-001", "customer_id": "CUS-001", "subject": "Consulta de entrega", "status": "abierto", "priority": "normal", "assigned_team": "Logística", "sla": "24 horas", "messages": ["Cliente pregunta por la entrega", "Equipo revisará la guía SHP-001"]}],
    "productos": [{"sku": "SKU-001", "name": "Audífonos Demo", "stock": 42, "price": 1499, "currency": "MXN", "warranty": "12 meses", "manual": "Cargar antes del primer uso", "compatibility": ["Bluetooth", "USB-C"], "alternatives": ["SKU-002"], "reviews": ["4.7/5 en opiniones simuladas"]}],
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


def make_tool(area: str, name: str, fields: str) -> Tool:
    # Pydantic genera un schema distinto por operación y valida los argumentos.
    arguments = create_model(name + "_arguments", **{key: PARAMETERS[key] for key in fields.split()}, **OPTIONS)

    def run(ctx: RunContext, **kwargs) -> dict:
        try:
            request = arguments.model_validate(kwargs).model_dump()
        except ValidationError as error:
            raise ModelRetry(str(error)) from error
        # Lectura: filtra los datos ficticios por los identificadores recibidos.
        if name in READ_TOOL_NAMES:
            filters = {key: request[key] for key in fields.split() if key != "query"}
            records = [row for row in DATA[area] if all(row.get(key) == value for key, value in filters.items())]
            if query := request.get("query"):
                records = [row for row in records if query.casefold() in str(row).casefold()]
            return {"simulated": True, "operation": name, "found": bool(records), "records": records}
        # Escritura: no cambia datos, solo registra la solicitud con un folio.
        entry = {"simulated": True, "operation": name, "request_id": f"REQ-{len(ctx.deps.service_requests) + 1:03}", "status": "solicitud registrada", "arguments": request}
        ctx.deps.service_requests.append(entry)
        return entry

    # El mismo handler sirve a las 80 tools; lo que cambia entre ellas es el schema que ve el modelo.
    return Tool.from_schema(run, name=name, description=CUSTOMER_CATALOG[name], json_schema=arguments.model_json_schema(), takes_ctx=True, sequential=True)


CUSTOMER_TOOLS = [make_tool(area, name, fields) for area, rows in OPERATIONS.items() for name, _, fields in rows]
