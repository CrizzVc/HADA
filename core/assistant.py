"""Cerebro del asistente: gestión de conversación con Ollama y llamada a herramientas."""
import json
import re
from typing import Dict, Generator, List, Optional, Tuple
import requests

from config import DEFAULT_MODEL, OLLAMA_HOST
from tools import tool_manager
from .prompt import SYSTEM_PROMPT

class HadaAssistant:
    def __init__(self, model: str = DEFAULT_MODEL, host: str = OLLAMA_HOST):
        self.model = model
        self.host = host.rstrip("/")
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def check_connection(self) -> Tuple[bool, str]:
        """Comprueba si el servidor de Ollama está encendido y accesible y valida el modelo."""
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=3)
            if r.status_code == 200:
                raw_models = r.json().get("models", [])
                models = [m.get("name") for m in raw_models]
                
                if not models:
                    return True, "Conectado a Ollama, pero no hay ningún modelo descargado (ejecuta 'ollama pull qwen2.5-coder:3b')."

                # Comprobar si el modelo configurado está disponible
                # (puede ser coincidencia exacta o sin etiqueta :latest)
                model_match = None
                for m in models:
                    if m == self.model or m.split(":")[0] == self.model.split(":")[0]:
                        model_match = m
                        break
                
                if model_match:
                    self.model = model_match
                else:
                    # Auto-asignar el primer modelo disponible
                    self.model = models[0]

                return True, f"Conectado a Ollama. Usando modelo: '[bold green]{self.model}[/bold green]' (disponibles: {', '.join(models)})"
            return False, f"Ollama respondió con código de estado {r.status_code}."
        except requests.exceptions.ConnectionError:
            return False, (
                f"No se pudo conectar a Ollama en {self.host}.\n"
                "Asegúrate de que Ollama esté abierto en segundo plano o ejecuta 'ollama serve'."
            )
        except Exception as e:
            return False, f"Error al verificar Ollama: {e}"

    def reset_chat(self):
        """Reinicia el historial de la conversación."""
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def chat_stream(self, user_text: str) -> Generator[Tuple[str, Optional[str]], None, None]:
        """Envía un mensaje a Ollama con streaming.
        
        Yields:
            Tupla (token_actual, oracion_completa_o_None):
            - token_actual: fragmento de texto para mostrar en pantalla en tiempo real.
            - oracion_completa_o_None: si se completó una frase lista para ser hablada por TTS.
        """
        self.history.append({"role": "user", "content": user_text})
        tools = tool_manager.get_ollama_tools()

        payload = {
            "model": self.model,
            "messages": self.history,
            "stream": True,
            "tools": tools,
            "options": {
                "temperature": 0.75,
                "top_p": 0.9,
                "presence_penalty": 0.4,
            },
        }

        try:
            res = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                stream=True,
                timeout=60
            )
        except Exception as e:
            error_msg = f"Error al conectar con Ollama: {e}"
            yield (error_msg, error_msg)
            return

        if res.status_code != 200:
            error_msg = f"Error de Ollama ({res.status_code}): {res.text}"
            yield (error_msg, error_msg)
            return

        full_reply = ""
        sentence_buffer = ""
        tool_calls_buffer: List[Dict] = []

        # Expresión regular para detectar fin de oraciones (., !, ?, \n)
        sentence_end_regex = re.compile(r"([.!?\n]+)\s*")

        for line in res.iter_lines():
            if not line:
                continue
            try:
                chunk = json.loads(line.decode("utf-8"))
            except Exception:
                continue

            msg = chunk.get("message", {})
            content = msg.get("content", "")
            
            # Detectar si el modelo solicitó invocar herramientas (Tool Calling)
            if "tool_calls" in msg and msg["tool_calls"]:
                tool_calls_buffer.extend(msg["tool_calls"])

            if content:
                full_reply += content
                sentence_buffer += content

                # Comprobar si completamos una frase natural para alimentar al TTS
                match = sentence_end_regex.search(sentence_buffer)
                if match:
                    end_idx = match.end()
                    candidate = sentence_buffer[:end_idx].strip()
                    words = candidate.split()

                    # Evitar cortes bruscos con fragmentos de 1 o 2 palabras:
                    # Exigir al menos 4 palabras (o salto de línea) para que Kokoro
                    # sintetice una curva melódica fluida en lugar de palabras sueltas.
                    if len(words) >= 4 or "\n" in candidate:
                        sentence_buffer = sentence_buffer[end_idx:]
                        yield (content, candidate)
                    else:
                        yield (content, None)
                else:
                    yield (content, None)

        # Si quedaron palabras al final sin puntuación de cierre
        remaining = sentence_buffer.strip()
        if remaining:
            yield ("", remaining)

        # Guardar respuesta del asistente en el historial
        self.history.append({"role": "assistant", "content": full_reply})

        # Si el modelo ejecutó herramientas, las procesamos y obtenemos el resultado
        if tool_calls_buffer:
            for tc in tool_calls_buffer:
                func_info = tc.get("function", {})
                name = func_info.get("name")
                args = func_info.get("arguments", {})
                
                status_text = f"\n[Acción ejecutada: {name}]"
                yield (status_text, None)
                
                result = tool_manager.execute_tool(name, args)
                yield (f"\nResultado: {result}\n", result)
                
                # Agregar el resultado al historial de mensajes
                self.history.append({
                    "role": "tool",
                    "content": str(result),
                })

