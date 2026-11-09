"""Gestor y registro de herramientas para HADA (Function Calling para Ollama)."""
from typing import Any, Callable, Dict, List
from .media_tools import play_or_pause_music, next_track, previous_track, search_spotify
from .web_tools import get_weather, search_google
from .system_tools import open_application, close_application

class ToolManager:
    def __init__(self):
        self._registry: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []
        self._register_default_tools()

    def register(self, name: str, description: str, parameters: Dict[str, Any], func: Callable):
        """Registra una función como herramienta accesible para Ollama."""
        self._registry[name] = func
        self._schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        })

    def _register_default_tools(self):
        # 1. Multimedia
        self.register(
            name="play_or_pause_music",
            description="Pausa o reanuda la música que esté reproduciéndose en el PC (Spotify, YouTube, etc.).",
            parameters={"type": "object", "properties": {}, "required": []},
            func=play_or_pause_music
        )
        self.register(
            name="next_track",
            description="Pasa a la siguiente canción en la cola de reproducción.",
            parameters={"type": "object", "properties": {}, "required": []},
            func=next_track
        )
        self.register(
            name="previous_track",
            description="Vuelve a la canción anterior.",
            parameters={"type": "object", "properties": {}, "required": []},
            func=previous_track
        )
        self.register(
            name="search_spotify",
            description="Busca y reproduce una canción, artista, álbum o playlist en Spotify.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Nombre de la canción, artista o género a buscar."
                    }
                },
                "required": ["query"]
            },
            func=search_spotify
        )

        # 2. Clima y Web
        self.register(
            name="get_weather",
            description="Consulta el pronóstico del clima actual y temperatura para una ciudad.",
            parameters={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Nombre de la ciudad (ej: Madrid, Bogotá, Buenos Aires, etc.)"
                    }
                },
                "required": ["city"]
            },
            func=get_weather
        )
        self.register(
            name="search_google",
            description="Abre el navegador web para realizar una búsqueda en Google.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Texto o pregunta a buscar en Google."
                    }
                },
                "required": ["query"]
            },
            func=search_google
        )

        # 3. Aplicaciones de Windows
        self.register(
            name="open_application",
            description="Abre un programa o ventana en Windows (calculadora, bloc de notas, chrome, spotify, etc.).",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Nombre de la aplicación a abrir (ej: calculadora, bloc de notas, chrome)."
                    }
                },
                "required": ["app_name"]
            },
            func=open_application
        )
        self.register(
            name="close_application",
            description="Cierra un programa o ventana en Windows.",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Nombre de la aplicación a cerrar."
                    }
                },
                "required": ["app_name"]
            },
            func=close_application
        )

    def get_ollama_tools(self) -> List[Dict[str, Any]]:
        """Retorna las herramientas registradas en el formato que espera Ollama."""
        return self._schemas

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Ejecuta una herramienta por nombre con sus argumentos."""
        func = self._registry.get(name)
        if not func:
            return f"Herramienta '{name}' no encontrada."
        try:
            return str(func(**arguments))
        except Exception as e:
            return f"Error ejecutando '{name}': {e}"

tool_manager = ToolManager()

