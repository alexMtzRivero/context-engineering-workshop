"""Genera conversacion-muy-larga.json: un análisis de cinco casos de soporte casi idénticos.

Uso: python datasets/generar_muy_larga.py [clientes] [--encabezados]
La conversación empieza con un pedido de análisis: encontrar la falla del proceso que produjo cinco
casos parecidos. Después vienen, una tras otra, las conversaciones completas con cada cliente.
Nébula Software es el caso original; los otros cuatro cambian el cliente, las personas, los números
de los identificadores, las fechas, las horas, el monto y la dirección. Los puestos 01 a 32 se
repiten en todos los casos: esos casi duplicados son los distractores que deterioran las respuestas.

Por defecto los casos van uno tras otro, sin encabezado. Con --encabezados, cada caso empieza con
"Siguiente caso: <cliente>"; esa estructura ayuda al modelo a separarlos y Haiku 5.5 deja de fallar.
"""

import sys

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
ORIGINAL = "Nébula Software"
DOMINIO = "nebula.example"
NOMBRES = ["Valeria Ortiz", "Paula Ramos", "Diego Salas", "Mario León", "Sonia Méndez", "Laura Peña"]
# (cliente, dominio de correo, las seis personas de su caso)
OTROS = [
    ("Despacho Ruiz Contadores", "ruizcontadores.example",
     ["Lucía Vega", "Andrea Soto", "Tomás Ruiz", "Iván Mora", "Elena Cruz", "Rocío Lara"]),
    ("Clínica Dental Sonrisa", "sonrisa.example",
     ["Marta Gil", "Carla Ríos", "Pablo Nieto", "Raúl Vidal", "Inés Prado", "Noelia Paz"]),
    ("Agencia Pixel", "agenciapixel.example",
     ["Sara Molina", "Julia Campos", "Hugo Serra", "Óscar Rey", "Alba Nuñez", "Clara Ibáñez"]),
    ("Hotel Mirador", "hotelmirador.example",
     ["Rosa Medina", "Irene Pastor", "Bruno Lago", "Félix Ortega", "Lidia Marín", "Gloria Fuentes"]),
    ("Constructora Altamira", "altamira.example",
     ["Ana Cano", "Beatriz Mora", "Adrián Gallo", "Jorge Bravo", "Silvia Rojas", "Pilar Santos"]),
    ("Laboratorios Vértice", "vertice.example",
     ["Elisa Duarte", "Mónica Salinas", "Rubén Castro", "Ernesto Vela", "Teresa Rivas", "Lorena Quiroga"]),
    ("Restaurante La Huerta", "lahuerta.example",
     ["Natalia Ferrer", "Olga Benítez", "Samuel Ponce", "Arturo Lemus", "Diana Ochoa", "Fernanda Arce"]),
]
ID = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")
INICIO = [
    {"role": "user", "content": (
        "Necesito tu ayuda con un análisis de procesos. En las últimas semanas atendimos cinco casos casi iguales: "
        "pedidos de 40 audífonos para capacitaciones internas, con unidades faltantes y dañadas, entregas reprogramadas "
        "y cobros duplicados. Sospechamos que hay una falla en nuestro proceso. Te voy a compartir, una tras otra, las "
        "conversaciones completas de soporte con cada cliente; en ellas habla el cliente y responde nuestro agente. Al "
        "final quiero un reporte de qué pasó en cada caso y qué tienen en común. Todos los datos son ficticios.")},
    {"role": "assistant", "content": (
        "De acuerdo. Revisaré los cinco casos en el orden en que los compartas y mantendré separados el cliente, los "
        "pedidos y los identificadores de cada uno. Cuando termines, preparo el reporte con lo que tienen en común.")},
]


def shift_digits(token: str, k: int) -> str:
    # Cambia cada grupo de dígitos de un identificador conservando su largo: DOCK-CAB-14 pasa a DOCK-CAB-21.
    return re.sub(r"\d+", lambda m: str((int(m.group()) + 7 * k) % 10 ** len(m.group())).zfill(len(m.group())), token)


def variante(text: str, k: int) -> str:
    cliente, dominio, personas = OTROS[k - 1]
    text = text.replace(ORIGINAL, cliente).replace(DOMINIO, dominio)
    for viejo, nuevo in zip(NOMBRES, personas):
        text = text.replace(viejo, nuevo).replace(viejo.split()[0], nuevo.split()[0])
    text = ID.sub(lambda m: shift_digits(m.group(), k) if re.search(r"\d", m.group()) else m.group(), text)
    text = re.sub(r"\b(1[5-9]|20) de octubre", lambda m: f"{int(m.group(1)) + k} de octubre", text)
    text = re.sub(r"\b(\d{2}):(\d{2})\b", lambda m: f"{(int(m.group(1)) + k % 3 + 1) % 24:02d}:{m.group(2)}", text)
    text = re.sub(r"\b31,644\.80\b", f"{31644.80 + 1111 * k:,.2f}", text)
    return text.replace("Laboratorio 240", f"Laboratorio {240 + 13 * k}")


def main(clientes=5, separadores=False, salida=HERE / "conversacion-muy-larga.json"):
    data = json.loads((HERE / "conversacion-larga.json").read_text())
    base = data["messages"]
    # El caso original queda a la mitad, donde más se pierde la atención.
    otros = list(range(1, clientes))
    orden = otros[: len(otros) // 2] + [0] + otros[len(otros) // 2:]
    mensajes = list(INICIO)
    for k in orden:
        cliente = ORIGINAL if k == 0 else OTROS[k - 1][0]
        if separadores:
            mensajes += [
                {"role": "user", "content": f"Siguiente caso: {cliente}. Esta es la conversación completa de soporte."},
                {"role": "assistant", "content": f"Recibido. Reviso el caso de {cliente} sin mezclarlo con los anteriores."},
            ]
        mensajes += [{"role": m["role"], "content": m["content"] if k == 0 else variante(m["content"], k)} for m in base]
    data.update(
        id="nebula-conversacion-muy-larga-v2",
        title="Análisis de cinco casos casi idénticos; Nébula Software a la mitad",
        description="Pedido de análisis de procesos y cinco conversaciones de soporte completas. Generado con generar_muy_larga.py.",
        messages=mensajes,
    )
    salida.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(salida.name, len(mensajes), "mensajes,", sum(len(m["content"]) for m in mensajes), "caracteres")


if __name__ == "__main__":
    numeros = [int(a) for a in sys.argv[1:] if a.isdigit()]
    main(clientes=numeros[0] if numeros else 5, separadores="--encabezados" in sys.argv)
