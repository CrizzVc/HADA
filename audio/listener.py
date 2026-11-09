"""Módulo de captura de micrófono y reconocimiento de voz (STT) con Vosk."""
import json
import os
import queue
import sys
from typing import Optional

from config import AUDIO_SAMPLE_RATE, VOSK_MODEL_PATH

class VoskListener:
    def __init__(self, model_path: str = VOSK_MODEL_PATH, sample_rate: int = AUDIO_SAMPLE_RATE):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.model = None
        self.audio_queue = queue.Queue()

    def is_model_available(self) -> bool:
        """Verifica si la carpeta del modelo de Vosk existe."""
        return os.path.exists(self.model_path) and os.path.isdir(self.model_path)

    def load_model(self) -> bool:
        """Carga el modelo de Vosk en memoria."""
        if self.model is not None:
            return True
        if not self.is_model_available():
            return False
        try:
            from vosk import Model
            self.model = Model(self.model_path)
            return True
        except Exception:
            return False

    def _audio_callback(self, indata, frames, time, status):
        """Callback llamado por sounddevice para cada bloque de audio."""
        if status:
            print(f"Estado de audio: {status}", file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def listen_once(self, timeout_seconds: int = 10) -> Optional[str]:
        """Escucha por el micrófono hasta que el usuario termina de hablar una frase.
        
        Retorna:
            El texto reconocido o None si no se reconoció nada.
        """
        if not self.load_model():
            return None

        try:
            import sounddevice as sd
            from vosk import KaldiRecognizer
        except ImportError:
            return None

        recognizer = KaldiRecognizer(self.model, self.sample_rate)
        # Limpiar cola previa
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()

        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=8000,
                dtype="int16",
                channels=1,
                callback=self._audio_callback
            ):
                while True:
                    data = self.audio_queue.get(timeout=timeout_seconds)
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "").strip()
                        if text:
                            return text
                    else:
                        # Resultado parcial (opcional para feedback)
                        pass
        except queue.Empty:
            # Si se agotó el tiempo de espera sin audio
            final_res = json.loads(recognizer.FinalResult())
            text = final_res.get("text", "").strip()
            return text if text else None
        except Exception as e:
            print(f"Error al capturar audio: {e}")
            return None

