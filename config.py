"""Configuración central para HADA (Asistente de IA local)."""
import os
from pathlib import Path

# Rutas del proyecto
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
VOSK_DIR = MODELS_DIR / "vosk"
KOKORO_DIR = MODELS_DIR / "kokoro"

# Configuración de Ollama (LLM)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
# Modelo configurado: si no existe, HADA intentará autodetectar el primer modelo disponible en Ollama
DEFAULT_MODEL = os.getenv("HADA_MODEL", "qwen2.5-coder:3b")

# Configuración de Vosk (STT)
# Modelo en español sugerido: vosk-model-small-es-0.42
VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", str(VOSK_DIR / "vosk-model-small-es-0.42"))
AUDIO_SAMPLE_RATE = 16000  # Frecuencia requerida por Vosk

# Configuración de Kokoro ONNX (TTS)
KOKORO_MODEL_FILE = os.getenv("KOKORO_MODEL_FILE", str(KOKORO_DIR / "kokoro-v1.0.onnx"))
KOKORO_VOICES_FILE = os.getenv("KOKORO_VOICES_FILE", str(KOKORO_DIR / "voices-v1.0.bin"))
# Voces disponibles: estándar ('ef_dora', 'em_alex') o personalizadas en 'voices/' ('Dj_Livi', 'hada_suave')
KOKORO_VOICE = os.getenv("KOKORO_VOICE", "Dj_Livi")
KOKORO_LANG = "es"
# Velocidad de voz: 1.05 es el punto óptimo para el ritmo ágil y dinámico estilo DJ Livi
KOKORO_SPEED = float(os.getenv("KOKORO_SPEED", "1.05"))

# Comportamiento por defecto
DEFAULT_VOICE_OUTPUT = True   # Si debe hablar además de escribir
ASSISTANT_NAME = "Hada"
