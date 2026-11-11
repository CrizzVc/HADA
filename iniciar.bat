@echo off
title HADA - Asistente Local
chcp 65001 > nul
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    echo [!] No se encontró el entorno virtual en .venv.
    echo Creando entorno e instalando dependencias...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
    python main.py
)
pause

