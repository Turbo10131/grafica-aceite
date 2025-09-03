#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Actualiza 'precio-aceite-historico.json' añadiendo la cotización del día
a partir del JSON público del otro repositorio:
https://raw.githubusercontent.com/Turbo10131/comparador-aceituna4/main/precio-aceite.json

Diseñado para ejecutarse a diario con GitHub Actions.
"""

import json
import sys
import urllib.request
from datetime import datetime, timezone

SOURCE_URL = "https://raw.githubusercontent.com/Turbo10131/comparador-aceituna4/main/precio-aceite.json"
DEST_FILE  = "precio-aceite-historico.json"

# Etiquetas “bonitas” usadas en el histórico
ETIQUETAS = {
    "virgen_extra": "Aceite de oliva virgen extra",
    "virgen":       "Aceite de oliva virgen",
    "lampante":     "Aceite de oliva lampante",
}

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))

def load_historico(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_historico(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hoy_iso():
    # usa fecha UTC; si quieres Europa/Madrid, cambia aquí
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def existe_fecha(lista, fecha):
    return any(item.get("fecha") == fecha for item in lista)

def normaliza_valor(x):
    try:
        v = float(x)
        # sanity check
        if 0 < v < 20:
            return round(v, 3)
    except Exception:
        pass
    return None

def main():
    try:
        historico = load_historico(DEST_FILE)
    except FileNotFoundError:
        print(f"[WARN] {DEST_FILE} no existe todavía. Crea uno con históricos iniciales.")
        return 0

    try:
        src = fetch_json(SOURCE_URL)
    except Exception as e:
        print(f"[ERROR] No se pudo descargar {SOURCE_URL}: {e}")
        return 1

    # El JSON fuente suele ser: {"fecha": "...", "precios": { "Aceite de oliva virgen extra": {precio_eur_kg: ...}, ... } }
    precios = (src or {}).get("precios") or {}

    # fecha de “hoy” para la entrada que añadiremos
    fecha_hoy = hoy_iso()

    actualizado = False

    for key_corta, etiqueta in ETIQUETAS.items():
        lista = historico.get(etiqueta, [])
        # si ya existe la fecha de hoy en esa serie, saltamos
        if existe_fecha(lista, fecha_hoy):
            continue

        # localizar en el JSON fuente con la etiqueta larga
        nodo = precios.get(etiqueta)
        if not nodo:
            # a veces pueden usar claves distintas; nada grave
            continue

        valor = normaliza_valor(nodo.get("precio_eur_kg"))
        if valor is None:
            continue

        lista.append({"fecha": fecha_hoy, "precio_eur_kg": valor})
        # mantener orden ascendente por fecha
        lista.sort(key=lambda d: d.get("fecha", ""))
        historico[etiqueta] = lista
        actualizado = True

    if actualizado:
        save_historico(historico, DEST_FILE)
        print(f"[OK] {DEST_FILE} actualizado con la fecha {fecha_hoy}.")
    else:
        print("[INFO] No había nada nuevo que añadir hoy.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
