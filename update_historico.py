#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convierte el histórico en texto plano (como el que tienes ahora) a un JSON válido.
Lee:  precio-aceite-historico.json   (aunque sea texto)
Escribe: precio-aceite-historico.json (JSON con 3 series)
"""

import re
import json
from datetime import datetime
from pathlib import Path

# Archivos
SRC_FILE = Path("precio-aceite-historico.json")   # actualmente es texto
OUT_FILE = Path("precio-aceite-historico.json")   # lo SOBREESCRIBIMOS ya en JSON

# Patrones
re_fecha = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")  # 26-08-2025
re_precio = re.compile(r"(\d+[.,]\d+|\d+)")          # 3.833 / 3,833 / 3

# Mapea las líneas de texto a nuestras claves JSON
TIPOS = {
    "virgen extra": "Aceite de oliva virgen extra",
    # OJO: "virgen" a secas debe ir DESPUÉS de "virgen extra" para no comer el 'extra'
    "virgen":       "Aceite de oliva virgen",
    "lampante":     "Aceite de oliva lampante",
}

def normaliza_num(txt: str) -> float:
    m = re_precio.search(txt)
    if not m:
        return None
    return float(m.group(1).replace(",", "."))

def detecta_tipo(line: str) -> str | None:
    low = line.lower()
    # primero chequeamos "virgen extra"
    if "virgen extra" in low:
        return TIPOS["virgen extra"]
    # luego "virgen"
    if " virgen " in f" {low} " or low.strip().startswith("aceite de oliva virgen "):
        return TIPOS["virgen"]
    # luego "lampante"
    if "lampante" in low:
        return TIPOS["lampante"]
    return None

def main():
    if not SRC_FILE.exists():
        raise SystemExit(f"No existe {SRC_FILE} en el repo.")

    # Estructura de salida
    data = {
        "Aceite de oliva virgen extra": [],
        "Aceite de oliva virgen": [],
        "Aceite de oliva lampante": [],
    }

    current_date_iso = None

    # Leemos el fuente línea a línea (texto)
    with SRC_FILE.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()

            # 1) Fecha
            mf = re_fecha.match(line)
            if mf:
                dd, mm, yyyy = mf.groups()
                try:
                    current_date_iso = datetime(int(yyyy), int(mm), int(dd)).strftime("%Y-%m-%d")
                except ValueError:
                    current_date_iso = None
                continue

            # 2) Líneas con "Sin cierre de operaciones" -> ignorar
            if "sin cierre de operaciones" in line.lower():
                continue

            # 3) Detectar tipo y extraer precio
            tipo = detecta_tipo(line)
            if not tipo:
                continue

            price = normaliza_num(line)
            if price is None:
                continue

            if current_date_iso:
                data[tipo].append({
                    "fecha": current_date_iso,
                    "precio_eur_kg": price
                })

    # Ordenamos por fecha ascendente cada serie
    for key in data:
        data[key].sort(key=lambda x: x["fecha"])

    # Guardamos en JSON bonico
    with OUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"OK: generado JSON en {OUT_FILE} con {len(data['Aceite de oliva virgen extra'])} VE,"
          f" {len(data['Aceite de oliva virgen'])} V, {len(data['Aceite de oliva lampante'])} L.")

if __name__ == "__main__":
    main()
