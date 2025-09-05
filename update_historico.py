# update_historico.py
import json
import os
import subprocess

DEST_JSON = "precio-aceite-historico.json"
SRC_TXT   = "historico.txt"

def es_json_valido(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            json.load(f)
        return True
    except Exception:
        return False

def main():
    # 1) Si el "JSON" en repo es texto crudo, conviértelo a TXT fuente
    if os.path.exists(DEST_JSON) and not es_json_valido(DEST_JSON):
        print(f"[WARN] {DEST_JSON} no es JSON. Lo muevo a {SRC_TXT}…")
        # Si ya existiera un historico.txt previo, lo sobreescribimos
        if os.path.exists(SRC_TXT):
            os.remove(SRC_TXT)
        os.rename(DEST_JSON, SRC_TXT)

    # 2) Si no hay fuente TXT, no podemos convertir
    if not os.path.exists(SRC_TXT):
        raise SystemExit(f"No existe {SRC_TXT}. Debes guardar aquí el texto crudo.")

    # 3) Ejecuta convertidor
    print("[INFO] Ejecutando convertir_historico.py…")
    subprocess.check_call(["python", "convertir_historico.py"])

    # 4) Valida JSON final
    if not es_json_valido(DEST_JSON):
        raise SystemExit(f"{DEST_JSON} generado no es JSON válido.")

    print("[OK] Histórico actualizado y validado.")

if __name__ == "__main__":
    main()
