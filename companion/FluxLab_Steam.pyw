"""Abre Trove y, escondido, el companion de FluxLab. Se cierra solo al cerrar Trove.

Se usa desde Steam: Trove > Propiedades > Opciones de lanzamiento:
    "<ruta de pyw.exe>" "<ruta de esta carpeta>\\FluxLab_Steam.pyw" %command%

Steam cambia %command% por el comando del juego. Primero se abre el juego (pase lo
que pase con el companion) y despues el companion queda vigilando sin ventana.
Lo que hace queda anotado en %APPDATA%\\FluxLab\\companion.log.
"""
import os
import subprocess
import sys

game = sys.argv[1:]
if game:
    try:
        subprocess.Popen(game, cwd=os.path.dirname(game[0]) or None)
    except OSError:
        subprocess.Popen(game)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], "--steam"]
try:
    import fluxlab_companion
    fluxlab_companion.main()
except Exception as e:  # sin consola: lo dejamos en el log
    try:
        import traceback
        home = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "FluxLab")
        os.makedirs(home, exist_ok=True)
        with open(os.path.join(home, "companion.log"), "a", encoding="utf-8") as f:
            f.write("Error inesperado:\n" + traceback.format_exc())
    except OSError:
        pass
