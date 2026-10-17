"""Genera conversacion-muy-larga.json: el caso de Aula Norte entre siete casos casi idénticos.

Uso: python datasets/generar_muy_larga.py [bloques]
Cada bloque extra cambia el aula, los nombres, los números de los identificadores, las fechas,
las horas, el monto y la dirección. Los puestos 01 a 32 se repiten en todos los bloques:
esos casi duplicados son los distractores que deterioran las respuestas.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
AULAS = ["Aula Sur", "Aula Este", "Aula Oeste", "Aula Centro", "Aula Poniente", "Aula Oriente", "Aula Bajío",
         "Aula Costa", "Aula Sierra", "Aula Valle", "Aula Lago", "Aula Bosque", "Aula Puerto", "Aula Llano", "Aula Mesa"]
NOMBRES = ["Valeria Ortiz", "Paula Ramos", "Diego Salas", "Mario León", "Sonia Méndez", "Laura Peña"]
OTROS = [
    ["Lucía Vega", "Andrea Soto", "Tomás Ruiz", "Iván Mora", "Elena Cruz", "Rocío Lara"],
    ["Marta Gil", "Carla Ríos", "Pablo Nieto", "Raúl Vidal", "Inés Prado", "Noelia Paz"],
    ["Sara Molina", "Julia Campos", "Hugo Serra", "Óscar Rey", "Alba Nuñez", "Clara Ibáñez"],
    ["Rosa Medina", "Irene Pastor", "Bruno Lago", "Félix Ortega", "Lidia Marín", "Gloria Fuentes"],
    ["Ana Cano", "Beatriz Mora", "Adrián Gallo", "Jorge Bravo", "Silvia Rojas", "Pilar Santos"],
]
ID = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")


def shift_digits(token: str, k: int) -> str:
    # Cambia cada grupo de dígitos de un identificador conservando su largo: DOCK-CAB-14 pasa a DOCK-CAB-21.
    return re.sub(r"\d+", lambda m: str((int(m.group()) + 7 * k) % 10 ** len(m.group())).zfill(len(m.group())), token)


def variante(text: str, k: int) -> str:
    text = text.replace("Aula Norte", AULAS[(k - 1) % len(AULAS)])
    for viejo, nuevo in zip(NOMBRES, OTROS[(k - 1) % len(OTROS)]):
        text = text.replace(viejo, nuevo).replace(viejo.split()[0], nuevo.split()[0])
    text = ID.sub(lambda m: shift_digits(m.group(), k) if re.search(r"\d", m.group()) else m.group(), text)
    text = re.sub(r"\b(1[5-9]|20) de octubre", lambda m: f"{int(m.group(1)) + k} de octubre", text)
    text = re.sub(r"\b(\d{2}):(\d{2})\b", lambda m: f"{(int(m.group(1)) + k % 3 + 1) % 24:02d}:{m.group(2)}", text)
    text = re.sub(r"\b31,644\.80\b", f"{31644.80 + 1111 * k:,.2f}", text)
    return text.replace("Laboratorio 240", f"Laboratorio {240 + 13 * k}")


def main():
    bloques = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    data = json.loads((HERE / "conversacion-larga.json").read_text())
    base = data["messages"]
    medio = bloques // 2
    mensajes = []
    for posicion in range(bloques):
        # El caso original queda a la mitad, donde más se pierde la atención.
        k = 0 if posicion == medio else (posicion + 1 if posicion < medio else posicion)
        mensajes += [{"role": m["role"], "content": m["content"] if k == 0 else variante(m["content"], k)} for m in base]
    data.update(
        id=f"{data['id']}-muy-larga",
        title="Ocho casos casi idénticos; Aula Norte a la mitad",
        description=f"{bloques} casos con la misma estructura; Aula Norte es el bloque {medio + 1}. Generado con generar_muy_larga.py.",
        messages=mensajes,
    )
    salida = HERE / "conversacion-muy-larga.json"
    salida.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(salida.name, len(mensajes), "mensajes,", sum(len(m["content"]) for m in mensajes), "caracteres")


if __name__ == "__main__":
    main()
