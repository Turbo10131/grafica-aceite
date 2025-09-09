# -*- coding: utf-8 -*-
"""
Lee el archivo 'historico.txt' (raíz del repo) con tu formato de líneas
y genera 'precio-aceite-historico.json' (también en la raíz del repo)
en el formato que usa la web.

Formato de salida:
{
  "Aceite de oliva virgen extra": [{ "fecha": "YYYY-MM-DD", "precio_eur_kg": 3.123 }, ...],
  "Aceite de oliva virgen":       [{ ... }],
  "Aceite de oliva lampante":     [{ ... }]
}
"""

import json
import re
from datetime import datetime

INPUT_FILE  = "historico.txt"
OUTPUT_FILE = "precio-aceite-historico.json"

# Estructura de salida
data = {
    "Aceite de oliva virgen extra": [],
    "Aceite de oliva virgen": [],
    "Aceite de oliva lampante": []
}

# Regex para fecha "dd-mm-yyyy"
rgx_fecha = re.compile(r"^(\d{2})-(\d{2})-(\d{4})\s*$")

# Normaliza "3.333 €" / "3,333 €" -> 3.333
def parse_precio(txt):
    if txt is None:
        return None
    txt = txt.strip().replace("€", "").replace(" ", "")
    txt = txt.replace(",", ".")
    try:
        v = float(txt)
        # filtro básico para evitar valores basura
        if 0 < v < 50:
            return v
    except:
        pass
    return None

# Mapea texto de la línea a la clave del dataset
def clave_producto(linea):
    s = linea.lower()
    if "virgen extra" in s:
        return "Aceite de oliva virgen extra"
    if " virgen " in s and "extra" not in s:
        return "Aceite de oliva virgen"
    if "lampante" in s:
        return "Aceite de oliva lampante"
    return None

def main():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            lineas = [l.rstrip("\n") for l in f]
    except FileNotFoundError:
        raise SystemExit(f"No existe {INPUT_FILE} en la raíz del repo.")

    fecha_actual_iso = None

    for raw in lineas:
        linea = raw.strip()

        # Detecta fecha (ej: 31-07-2014)
        m = rgx_fecha.match(linea)
        if m:
            d, mth, y = m.groups()
            try:
                fecha_actual_iso = datetime(int(y), int(mth), int(d)).strftime("%Y-%m-%d")
            except ValueError:
                fecha_actual_iso = None
            continue

        if not linea or not fecha_actual_iso:
            continue

        # Ignora cabeceras/ruido
        lower = linea.lower()
        if "sin cierre de operaciones" in lower or "about:blank" in lower:
            continue
        if "tipo de aceite" in lower and "precio" in lower:
            continue

        # Intenta extraer producto y precio
        clave = clave_producto(linea)
        if not clave:
            continue

        # Precio suele ir como "... 3.333 €" -> nos quedamos con el último token con símbolo €
        tokens = [t for t in linea.replace(",", ".").split() if "€" in t]
        precio = parse_precio(tokens[-1] if tokens else None)
        if precio is None:
            continue

        data[clave].append({
            "fecha": fecha_actual_iso,
            "precio_eur_kg": round(precio, 3)
        })

    # Ordena por fecha ascendente en cada serie
    for k in data:
        data[k].sort(key=lambda x: x["fecha"])

    # Escribe JSON en la RAÍZ del repo
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        json.dump(data, out, ensure_ascii=False, indent=2)

    print(f"Generado {OUTPUT_FILE} con:")
    for k, v in data.items():
        print(f"  - {k}: {len(v)} puntos")

if __name__ == "__main__":
    main()
