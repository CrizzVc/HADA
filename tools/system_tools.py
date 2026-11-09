"""Herramientas de control del sistema Windows: abrir y cerrar aplicaciones."""
import os
import subprocess

COMMON_APPS = {
    "calculadora": "calc",
    "calc": "calc",
    "bloc de notas": "notepad",
    "notepad": "notepad",
    "explorador": "explorer",
    "explorador de archivos": "explorer",
    "chrome": "start chrome",
    "google chrome": "start chrome",
    "edge": "start msedge",
    "navegador": "start msedge",
    "spotify": "start spotify",
    "paint": "mspaint",
    "terminal": "start wt",
    "cmd": "start cmd",
}

EXE_KILL_NAMES = {
    "calculadora": "CalculatorApp.exe",
    "calc": "CalculatorApp.exe",
    "bloc de notas": "notepad.exe",
    "notepad": "notepad.exe",
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "spotify": "Spotify.exe",
    "paint": "mspaint.exe",
}

def open_application(app_name: str) -> str:
    """Abre una aplicación en Windows por su nombre (ej. calculadora, bloc de notas, chrome, spotify).
    
    Args:
        app_name: Nombre de la aplicación a abrir.
    """
    key = app_name.strip().lower()
    cmd = COMMON_APPS.get(key, f"start {key}")
    try:
        os.system(cmd)
        return f"Abriendo {app_name}..."
    except Exception as e:
        return f"Error al abrir {app_name}: {e}"

def close_application(app_name: str) -> str:
    """Cierra una aplicación abierta en Windows.
    
    Args:
        app_name: Nombre de la aplicación a cerrar (ej. bloc de notas, chrome, spotify).
    """
    key = app_name.strip().lower()
    exe_name = EXE_KILL_NAMES.get(key, f"{key}.exe")
    try:
        # taskkill /IM nombre.exe /F
        result = subprocess.run(
            ["taskkill", "/IM", exe_name, "/F"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            return f"{app_name} se ha cerrado correctamente."
        else:
            return f"No se encontró una ventana activa para {app_name} o no se pudo cerrar."
    except Exception as e:
        return f"Error al cerrar {app_name}: {e}"

