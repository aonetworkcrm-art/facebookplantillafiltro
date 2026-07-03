@echo off
title Afiliados AI Agent - Dashboard
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║     🚀  AFILIADOS AI AGENT - DASHBOARD          ║
echo ║                                                  ║
echo ║  Iniciando servidor en puerto auto-detectedo...  ║
echo ╚══════════════════════════════════════════════════╝
echo.

python run.py --dashboard

pause
