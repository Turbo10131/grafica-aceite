# convertir_historico.py
import json
import re
from datetime import datetime

SRC_TXT = "historico.txt"                    # <-- el TXT crudo
DEST_JSON = "precio-aceite-historico.json"   # <-- salida JSON

# Normaliza "3,455 €" -> 3.455 (float)
def _num(s: str):
    s = s.replace("€", "").replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except:
        return None

# Mapea una línea a tipo de aceite
def _tipo_desde_linea(line: str):
    l = line.lower()
    if "virgen extra" in l:
        return "Aceite de oliva virgen extra"
    if re.search(r"\bvirgen\b", l) and "extra" not in l:
        return "Aceite de oliva virgen"
    if "lampante" in l:
        return "Aceite de oliva lampante"
    return None

# Extrae "3.833" de "3.833 €" o "3,833 €"
def _precio_desde_linea(line: str):
    m = re.search(r"(\d+[.,]\d+)\s*€", line)
    if not m:
        return None
    return _num(m.group(1))

# Extrae fecha DD-MM-YYYY
re_fecha = re.compile(r"\b(\d{2}-\d{2}-\d{4})\b")

def _iso(dmy: str):
    d = datetime.strptime(dmy, "%d-%m-%Y").date()
    return d.isoformat()

def convertir():
    data = {
        "Aceite de oliva virgen extra": [],
        "Aceite de oliva virgen": [],
        "Aceite de oliva lampante": [],
    }

    # Leemos el TXT crudo
    with open(SRC_TXT, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    fecha_actual_iso = None
    # Limpiadores de ruido
    basura = (
        "tipo de aceite", "variedad", "precio €/kg",
        "sin cierre de operaciones", "about:blank"
    )

    for ln in lines:
        lo = ln.lower()
        # Salta cabeceras/ruido
        if any(b in lo for b in basura):
            continue

        # Captura fecha (si hay), y guarda como "fecha actual"
        m = re_fecha.search(ln)
        if m:
            try:
                fecha_actual_iso = _iso(m.group(1))
            except:
                fecha_actual_iso = None
            continue

        if not fecha_actual_iso:
            # No tenemos fecha asignada aún; continúa
            continue

        # Detecta tipo y precio en líneas de producto
        tipo = _tipo_desde_linea(ln)
        if not tipo:
            continue

        precio = _precio_desde_linea(ln)
        if precio is None:
            continue

        data[tipo].append({
            "fecha": fecha_actual_iso,
            "precio_eur_kg": round(precio, 3)
        })

    # Ordena por fecha y quita duplicados (misma fecha para un tipo)
    for k in data:
        seen = set()
        ordenados = []
        for item in sorted(data[k], key=lambda x: x["fecha"]):
            clave = item["fecha"]
            if clave in seen:
                # Si el mismo día aparece más de una vez, nos quedamos con el último
                ordenados[-1] = item
            else:
                seen.add(clave)
                ordenados.append(item)
        data[k] = ordenados

    with open(DEST_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"OK → {DEST_JSON} generado con {sum(len(v) for v in data.values())} puntos.")

if __name__ == "__main__":
    convertir()
