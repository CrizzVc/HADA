"""Herramientas de reproducción multimedia y Spotify."""
import ctypes
import os
import subprocess
import urllib.parse

# Códigos de teclas virtuales de Windows para multimedia
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

def _send_key(vk_code: int):
    """Envía una pulsación de tecla virtual en Windows usando ctypes (sin dependencias externas)."""
    user32 = ctypes.windll.user32
    user32.keybd_event(vk_code, 0, 0, 0)      # Key down
    user32.keybd_event(vk_code, 0, 2, 0)      # Key up (KEYEVENTF_KEYUP = 2)

def play_or_pause_music() -> str:
    """Pausa o reanuda la música que esté sonando en el PC (Spotify, YouTube, reproductor, etc.)."""
    try:
        _send_key(VK_MEDIA_PLAY_PAUSE)
        return "Comando de reproducir/pausar enviado a Windows."
    except Exception as e:
        return f"Error al pausar o reproducir música: {e}"

def next_track() -> str:
    """Pasa a la siguiente canción en el reproductor multimedia."""
    try:
        _send_key(VK_MEDIA_NEXT_TRACK)
        return "Siguiente canción."
    except Exception as e:
        return f"Error al pasar de canción: {e}"

def previous_track() -> str:
    """Vuelve a la canción anterior en el reproductor multimedia."""
    try:
        _send_key(VK_MEDIA_PREV_TRACK)
        return "Canción anterior."
    except Exception as e:
        return f"Error al retroceder canción: {e}"

def search_spotify(query: str) -> str:
    """Busca y abre una canción, artista o lista en la aplicación de Spotify.
    
    Args:
        query: Nombre de la canción, artista o álbum a buscar.
    """
    try:
        safe_query = urllib.parse.quote(query)
        # Intenta abrir mediante el protocolo nativo de Spotify en Windows
        uri = f"spotify:search:{safe_query}"
        os.system(f"start {uri}")
        return f"Buscando '{query}' en Spotify."
    except Exception as e:
        return f"Error al abrir Spotify: {e}"

