"""FluxLab Companion: envia a tu cuenta de FluxLab las sesiones del mod FluxLab Tracker.

Vigila %APPDATA%\\Trove\\ModCfgs\\FluxLab Tracker.cfg. Cuando le das "Terminar" en el
inventario de Trove, el mod escribe la sesion ahi y este programa la manda a la pagina.
No toca el juego: solo lee el archivo que el propio Trove escribe.

Uso:  py fluxlab_companion.py          (la primera vez te pide la direccion y la clave)
      py fluxlab_companion.py --config (para cambiarlas)
      py fluxlab_companion.py --steam  (modo escondido: lo usa FluxLab_Steam.pyw, se
                                        cierra solo cuando cierras Trove)
"""
import json
import os
import socket
import subprocess
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
LOG_FILE = os.path.join(HOME, "companion.log")
POLL_SECONDS = 2
RETRY_SECONDS = 30

# Modo Steam
GAME_EXES = ("trove.exe", "trove_x64.exe")
WAIT_FOR_GAME = 20 * 60      # Glyph puede tardar (login, parches) antes de abrir el juego
GAME_GONE_AFTER = 45         # segundos sin ver el juego para darlo por cerrado
FINAL_SEND_WINDOW = 4 * 60   # tras cerrar, cuanto insistir si queda una sesion sin enviar
PROCESS_CHECK_EVERY = 10
LOCK_PORT = 47831            # evita dos companions a la vez

_log_to_file = False


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    if _log_to_file:
        try:
            if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 200_000:
                os.replace(LOG_FILE, LOG_FILE + ".old")
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass
    else:
        print(line, flush=True)


def load_config(force=False, interactive=True):
    os.makedirs(HOME, exist_ok=True)
    cfg = {}
    if os.path.exists(CONFIG):
        with open(CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
    if (force or not cfg.get("url") or not cfg.get("key")) and interactive:
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


class Watcher:
    """Lee el archivo del mod y manda las sesiones terminadas que falten."""

    def __init__(self, cfg):
        self.cfg = cfg
        os.makedirs(HOME, exist_ok=True)
        self.sent = load_sent()
        self.last_seen = None
        self.retry_at = 0.0

    def _done(self, value):
        mark_sent(value)
        self.sent.add(value)

    def step(self):
        """Una pasada. Devuelve True si queda una sesion terminada sin enviar."""
        value = read_session_line()
        if value and value != self.last_seen:
            if value.startswith("start|"):
                log("Sesion en curso...")
            self.last_seen = value
        if not (value and value.startswith("end|") and value not in self.sent):
            return False
        if time.time() < self.retry_at:
            return True
        try:
            res = send(self.cfg, value)
            self._done(value)
            fph = res.get("flux_per_hour")
            log(f"Sesion enviada: +{res['flux']:,} flux en {res['minutes']} min"
                + (f" ({fph:,} flux/h)" if fph else "") + f"  {res.get('url', '')}")
            return False
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:200]
            if e.code == 401:
                log("La clave no es valida. Corre el programa con --config y pega una clave nueva.")
                self.retry_at = time.time() + 3600
                return False  # no tiene sentido insistir con una clave mala
            if 400 <= e.code < 500:
                log(f"FluxLab rechazo la sesion ({e.code}): {detail}. No se reintenta.")
                self._done(value)
                return False
            log(f"Error del servidor ({e.code}); reintento en {RETRY_SECONDS} s.")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            log(f"Sin conexion con FluxLab ({e}); reintento en {RETRY_SECONDS} s.")
        except (ValueError, KeyError):
            log(f"Linea de sesion con formato raro, se ignora: {value}")
            self._done(value)
            return False
        self.retry_at = time.time() + RETRY_SECONDS
        return True


def game_running():
    """True si Trove esta abierto. None si no se pudo mirar."""
    try:
        out = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).stdout.lower()
    except (OSError, subprocess.SubprocessError):
        return None
    return any(f'"{exe}"' in out for exe in GAME_EXES)


def single_instance():
    """Devuelve un socket abierto si somos el unico companion, o None si ya hay otro."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", LOCK_PORT))
        s.listen(1)
        return s
    except OSError:
        s.close()
        return None


def run_normal(cfg):
    w = Watcher(cfg)
    log(f"Vigilando {MOD_CFG}")
    log("Dale EMPEZAR y TERMINAR en la franja FLUXLAB de la pestana de monedas. Ctrl+C para salir.")
    while True:
        w.step()
        time.sleep(POLL_SECONDS)


def run_steam(cfg, is_running=game_running, sleep=time.sleep, clock=time.monotonic):
    """Corre mientras Trove este abierto y se cierra solo despues."""
    w = Watcher(cfg)
    log("Modo Steam: esperando a que abra Trove.")
    start = clock()
    seen_game = False
    last_game = None
    last_check = -PROCESS_CHECK_EVERY
    closed_at = None
    while True:
        pending = w.step()
        now = clock()
        if now - last_check >= PROCESS_CHECK_EVERY:
            last_check = now
            running = is_running()
            if running is None:
                running = True  # si no podemos mirar, mejor seguir vivos
            if running:
                if not seen_game:
                    log("Trove abierto. Vigilando sesiones.")
                seen_game, last_game, closed_at = True, now, None
            elif not seen_game and now - start > WAIT_FOR_GAME:
                log("Trove no se abrio; me cierro.")
                return
            elif seen_game and closed_at is None and now - last_game > GAME_GONE_AFTER:
                closed_at = now
                log("Trove cerrado.")
        if closed_at is not None:
            if not pending:
                log("Nada pendiente; me cierro.")
                return
            if now - closed_at > FINAL_SEND_WINDOW:
                log("No se pudo enviar la ultima sesion; se enviara la proxima vez.")
                return
        sleep(POLL_SECONDS)


def main():
    global _log_to_file
    steam = "--steam" in sys.argv
    if steam:
        _log_to_file = True
        if single_instance_lock() is None:
            log("Ya hay un companion abierto; no abro otro.")
            return
        cfg = load_config(interactive=False)
        if not cfg.get("url") or not cfg.get("key"):
            log("Falta configurar: abre FluxLab.bat una vez y pon la direccion y la clave.")
            return
        run_steam(cfg)
    else:
        cfg = load_config(force="--config" in sys.argv)
        if single_instance_lock() is None:
            log("Ojo: ya hay otro companion abierto (quizas el de Steam). No pasa nada, "
                "las sesiones no se duplican.")
        run_normal(cfg)


_lock = None


def single_instance_lock():
    global _lock
    if _lock is None:
        _lock = single_instance()
    return _lock


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nHasta luego.")
