@echo off
title Afiliados AI Agent - Dashboard + Tunnel Público
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║     🚀  AFILIADOS AI AGENT - TUNNEL PÚBLICO     ║
echo ║                                                  ║
echo ║  Dashboard local + túnel Cloudflare              ║
echo ║  Accesible desde cualquier lugar GRATIS          ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo 🔗 El dashboard sera accesible desde internet
echo    via Cloudflare Tunnel (https://???).trycloudflare.com
echo.
echo ⚡ IMPORTANTE: Manten esta ventana abierta.
echo    Cerrar = detener el dashboard y el tunel.
echo.

python run.py --dashboard --tunnel

pause
