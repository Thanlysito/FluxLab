"""FluxLab Companion: envia a tu cuenta de FluxLab las sesiones del mod FluxLab Tracker.

Vigila %APPDATA%\\Trove\\ModCfgs\\FluxLab Tracker.cfg. Cuando le das "Terminar" en el
inventario de Trove, el mod escribe la sesion ahi y este programa la manda a la pagina.
No toca el juego: solo lee el archivo que el propio Trove escribe.

Uso:  py fluxlab_companion.py          (la primera vez te pide la direccion y la clave)
      py fluxlab_companion.py --config (para cambiarlas)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

APPDATA = os.environ.get("APPDATA", os.path.expanduser("~"))
MOD_CFG = os.path.join(APPDATA, "Trove", "ModCfgs", "FluxLab Tracker.cfg")
HOME = os.path.join(APPDATA, "FluxLab")
CONFIG = os.path.join(HOME, "config.json")
SENT = os.path.join(HOME, "enviadas.txt")
POLL_SECONDS = 2
RETRY_SECONDS = 30


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def load_config(force=False):
    os.makedirs(HOME, exist_ok=True)
    cfg = {}
    if os.path.exists(CONFIG):
        with open(CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
    if force or not cfg.get("url") or not cfg.get("key"):
        print("Configuracion de FluxLab Companion")
        url = input(f"Direccion de FluxLab [{cfg.get('url', 'https://fluxlab.onrender.com')}]: ").strip()
        cfg["url"] = (url or cfg.get("url") or "https://fluxlab.onrender.com").rstrip("/")
        key = input("Tu clave (FluxLab > Perfil > Generar clave): ").strip()
        if key:
            cfg["key"] = key
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        print(f"Guardado en {CONFIG}\n")
    return cfg


def read_session_line():
    """Devuelve el valor de 'session = ...' del archivo del mod, o None."""
    try:
        with open(MOD_CFG, encoding="utf-8", errors="replace") as f:
            for line in f:
                name, sep, value = line.partition("=")
                if sep and name.strip().lower() == "session":
                    return value.strip()
    except OSError:
        return None
    return None


def load_sent():
    try:
        with open(SENT, encoding="utf-8") as f:
            return {l.strip() for l in f if l.strip()}
    except OSError:
        return set()


def mark_sent(value):
    with open(SENT, "a", encoding="utf-8") as f:
        f.write(value + "\n")


def send(cfg, value):
    # end|fin|flux_fin|inicio|flux_inicio
    _, ended, flux_end, started, flux_start = value.split("|")[:5]
    body = json.dumps({
        "started_at": int(float(started)), "ended_at": int(float(ended)),
        "flux_start": int(float(flux_start)), "flux_end": int(float(flux_end)),
    }).encode()
    req = urllib.request.Request(
        cfg["url"] + "/api/sesiones/", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Token " + cfg["key"]},
    )
    # Render gratis tarda hasta un minuto en despertar.
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


def main():
    cfg = load_config(force="--config" in sys.argv)
    sent = load_sent()
    log(f"Vigilando {MOD_CFG}")
    log("Dale 'FluxLab: Empezar' y 'Terminar' en la pestana de monedas del inventario. Ctrl+C para salir.")
    last_seen, retry_at = None, 0.0
    while True:
        value = read_session_line()
        if value and value != last_seen:
            if value.startswith("start|"):
                log("Sesion en curso...")
            last_seen = value
        if value and value.startswith("end|") and value not in sent and time.time() >= retry_at:
            try:
                res = send(cfg, value)
                mark_sent(value)
                sent.add(value)
                fph = res.get("flux_per_hour")
                log(f"Sesion enviada: +{res['flux']:,} flux en {res['minutes']} min"
                    + (f" ({fph:,} flux/h)" if fph else "") + f"  {res.get('url', '')}")
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")[:200]
                if e.code == 401:
                    log("La clave no es valida. Corre el programa con --config y pega una clave nueva.")
                    retry_at = time.time() + 3600
                elif 400 <= e.code < 500:
                    log(f"FluxLab rechazo la sesion ({e.code}): {detail}. No se reintenta.")
                    mark_sent(value)
                    sent.add(value)
                else:
                    log(f"Error del servidor ({e.code}); reintento en {RETRY_SECONDS} s.")
                    retry_at = time.time() + RETRY_SECONDS
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                log(f"Sin conexion con FluxLab ({e}); reintento en {RETRY_SECONDS} s.")
                retry_at = time.time() + RETRY_SECONDS
            except ValueError:
                log(f"Linea de sesion con formato raro, se ignora: {value}")
                mark_sent(value)
                sent.add(value)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nHasta luego.")
