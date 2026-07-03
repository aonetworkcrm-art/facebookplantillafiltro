#!/usr/bin/env python3
"""
Inicia el dashboard con túnel público Cloudflare.
Muestra la URL para acceder desde cualquier lugar.
"""
import threading
import subprocess
import sys
import os
import time
import re
import signal

sys.path.insert(0, os.path.dirname(__file__))
from dashboard.api import app, find_free_port

port = find_free_port()
_cloudflared = None

def cleanup(signum=None, frame=None):
    global _cloudflared
    if _cloudflared:
        _cloudflared.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# ─── Iniciar Flask ────────────────────────────────────────────────
def run_flask():
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()
time.sleep(1.0)

# ─── BANNER ────────────────────────────────────────────────────────
print("")
print("╔══════════════════════════════════════════════════╗")
print("║     🚀  AFILIADOS AI AGENT                      ║")
print("╠══════════════════════════════════════════════════╣")
print(f"║  🌐 Local:    http://localhost:{port}                ║")
print(f"║  📊 API:      http://localhost:{port}/api/            ║")
print("╠══════════════════════════════════════════════════╣")
print("║  🔗 Abriendo túnel Cloudflare...                 ║")
print("║  Comparte la URL de abajo para acceder           ║")
print("║  desde CUALQUIER DISPOSITIVO                     ║")
print("╚══════════════════════════════════════════════════╝")
print("")

# ─── Iniciar Cloudflare Tunnel ───────────────────────────────────
try:
    tunnel_url = f"http://localhost:{port}"
    _cloudflared = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", tunnel_url],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    url_found = False
    start_time = time.time()
    timeout = 40

    for line in iter(_cloudflared.stdout.readline, ""):
        line = line.rstrip()
        if line:
            print(f"  {line}")

        match = re.search(r'https://[a-zA-Z0-9_-]+\.trycloudflare\.com', line)
        if match and not url_found:
            url_found = True
            public_url = match.group(0)
            print("")
            print("╔══════════════════════════════════════════════════╗")
            print("║     🎉  DASHBOARD PÚBLICO 🎉                    ║")
            print("╠══════════════════════════════════════════════════╣")
            print(f"║  {public_url:<45}║")
            print("╠══════════════════════════════════════════════════╣")
            print("║  Comparte esta URL para acceder desde           ║")
            print("║  cualquier dispositivo (móvil, otro PC)         ║")
            print("║                                                ║")
            print("║  El túnel está activo mientras esta ventana     ║")
            print("║  esté abierta. Ctrl+C para detener todo.       ║")
            print("╚══════════════════════════════════════════════════╝")
            print("")

        if time.time() - start_time > timeout:
            if not url_found:
                print("")
                print("⚠️  No se obtuvo URL pública automáticamente.")
                print(f"   Accede localmente: http://localhost:{port}")
                print("")
            break

except FileNotFoundError:
    print("")
    print("❌ cloudflared no está instalado.")
    print("   Instálalo gratis: winget install cloudflared")
    print(f"   Por ahora accede localmente: http://localhost:{port}")
    print("")

# Mantener vivo hasta Ctrl+C
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    cleanup()
