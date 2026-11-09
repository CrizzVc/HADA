"""Módulo de síntesis de voz (TTS) con Kokoro-ONNX y cola de reproducción."""
import os
import queue
import threading
from typing import Optional

from config import (
    DEFAULT_VOICE_OUTPUT,
    KOKORO_LANG,
    KOKORO_MODEL_FILE,
    KOKORO_VOICE,
    KOKORO_VOICES_FILE,
)

class KokoroSpeaker:
    def __init__(
        self,
        voice: str = KOKORO_VOICE,
        lang: str = KOKORO_LANG,
        model_file: str = KOKORO_MODEL_FILE,
        voices_file: str = KOKORO_VOICES_FILE,
        enabled: bool = DEFAULT_VOICE_OUTPUT
    ):
        self.voice = voice
        self.lang = lang
        self.model_file = model_file
        self.voices_file = voices_file
        self.enabled = enabled
        self.queue: queue.Queue[Optional[str]] = queue.Queue()
        self._kokoro = None
        self._fallback_sapi = None
        self._is_running = True
        
        # Iniciar hilo de reproducción en segundo plano
        self._worker_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self._worker_thread.start()

    def is_model_downloaded(self) -> bool:
        """Verifica si existen los archivos del modelo ONNX y las voces."""
        return os.path.exists(self.model_file) and os.path.exists(self.voices_file)

    def _init_tts(self):
        """Inicializa Kokoro-ONNX si los archivos existen; si no, recurre a SAPI de Windows."""
        if self._kokoro is not None or self._fallback_sapi is not None:
            return

        # 1. Intentar Kokoro ONNX
        if self.is_model_downloaded():
            try:
                from kokoro_onnx import Kokoro
                self._kokoro = Kokoro(self.model_file, self.voices_file)
                return
            except Exception:
                pass

        # 2. Fallback a voz de Windows SAPI si Kokoro aún no está descargado
        try:
            import win32com.client
            self._fallback_sapi = win32com.client.Dispatch("SAPI.SpVoice")
        except Exception:
            pass

    def _playback_worker(self):
        """Consume frases de la cola y las sintetiza/reproduce."""
        while self._is_running:
            sentence = self.queue.get()
            if sentence is None:
                break
            if not self.enabled or not sentence.strip():
                self.queue.task_done()
                continue

            try:
                self._init_tts()
                if self._kokoro is not None:
                    import sounddevice as sd
                    samples, sample_rate = self._kokoro.create(
                        sentence,
                        voice=self.voice,
                        speed=1.0,
                        lang=self.lang
                    )
                    sd.play(samples, sample_rate)
                    sd.wait()
                elif self._fallback_sapi is not None:
                    self._fallback_sapi.Speak(sentence)
            except Exception:
                # Silencioso si ocurre algún error de audio
                pass
            finally:
                self.queue.task_done()

    def speak(self, text: str):
        """Añade una frase a la cola para ser hablada."""
        if self.enabled and text.strip():
            self.queue.put(text.strip())

    def toggle(self) -> bool:
        """Activa o desactiva la voz del asistente."""
        self.enabled = not self.enabled
        return self.enabled

    def stop(self):
        """Detiene el hilo del reproductor."""
        self._is_running = False
        self.queue.put(None)
