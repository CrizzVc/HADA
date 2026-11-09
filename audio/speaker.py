"""Módulo de síntesis de voz (TTS) con Kokoro-ONNX, pre-renderizado en pipeline y recorte de silencios."""
import os
import queue
import re
import threading
from typing import Optional, Tuple
import numpy as np

from config import (
    DEFAULT_VOICE_OUTPUT,
    KOKORO_LANG,
    KOKORO_MODEL_FILE,
    KOKORO_SPEED,
    KOKORO_VOICE,
    KOKORO_VOICES_FILE,
)
from .voice_cloner import VoiceCloner

def clean_speech_text(text: str) -> str:
    """Limpia el texto antes de enviarlo a la síntesis de voz."""
    if not text:
        return ""
    # Eliminar bloques de acción entre corchetes
    text = re.sub(r"\[.*?\]", "", text)
    # Eliminar URLs
    text = re.sub(r"https?://\S+", "", text)
    # Eliminar caracteres markdown
    text = re.sub(r"[*_#`~>|-]", " ", text)
    
    # En español, '¡' y '¿' al inicio introducen pausas de vacilación excesivas en el motor fonético de Kokoro.
    # Las eliminamos para que el arranque sea inmediato y natural.
    text = text.replace("¡", "").replace("¿", "")
    
    # Las exclamaciones repetidas ('!!') o muy marcadas fuerzan pausas largas en Kokoro.
    # Las suavizamos a un punto o coma según contexto.
    text = re.sub(r"!+", ".", text)

    # Reemplazar múltiples espacios
    text = re.sub(r"\s+", " ", text).strip()
    return text

def trim_audio_silence(
    samples: np.ndarray,
    sample_rate: int = 24000,
    threshold: float = 0.015,
    keep_leading_ms: int = 20,
    keep_trailing_ms: int = 70
) -> np.ndarray:
    """Recorta el silencio excesivo tanto al inicio como al final de cada frase.
    
    Elimina las pausas largas que los signos de exclamación y puntuación agregan al audio.
    """
    if len(samples) == 0:
        return samples
    
    non_silent = np.where(np.abs(samples) > threshold)[0]
    if len(non_silent) == 0:
        return samples
    
    first_sound = non_silent[0]
    last_sound = non_silent[-1]
    
    leading_keep = int((keep_leading_ms / 1000.0) * sample_rate)
    trailing_keep = int((keep_trailing_ms / 1000.0) * sample_rate)
    
    start_idx = max(0, first_sound - leading_keep)
    end_idx = min(len(samples), last_sound + trailing_keep)
    
    return samples[start_idx:end_idx]

class KokoroSpeaker:
    def __init__(
        self,
        voice: str = KOKORO_VOICE,
        lang: str = KOKORO_LANG,
        speed: float = KOKORO_SPEED,
        model_file: str = KOKORO_MODEL_FILE,
        voices_file: str = KOKORO_VOICES_FILE,
        enabled: bool = DEFAULT_VOICE_OUTPUT
    ):
        self.voice = voice
        self.lang = lang
        self.speed = speed
        self.model_file = model_file
        self.voices_file = voices_file
        self.enabled = enabled
        self.cloner = VoiceCloner()
        
        # Dos colas: una para texto pendiente y otra para audio ya sintetizado
        self.text_queue: queue.Queue[Optional[str]] = queue.Queue()
        self.audio_queue: queue.Queue[Optional[Tuple[np.ndarray, int]]] = queue.Queue()
        
        self._kokoro = None
        self._fallback_sapi = None
        self._is_running = True
        
        # 1. Hilo que sintetiza audio por adelantado (para eliminar la espera de inferencia)
        self._synthesis_thread = threading.Thread(target=self._synthesis_worker, daemon=True)
        self._synthesis_thread.start()
        
        # 2. Hilo que reproduce el audio preparado inmediatamente
        self._playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self._playback_thread.start()

    def is_model_downloaded(self) -> bool:
        """Verifica si existen los archivos del modelo ONNX y las voces."""
        return os.path.exists(self.model_file) and os.path.exists(self.voices_file)

    def _init_tts(self):
        """Inicializa Kokoro-ONNX si los archivos existen; si no, recurre a SAPI de Windows."""
        if self._kokoro is not None or self._fallback_sapi is not None:
            return

        if self.is_model_downloaded():
            try:
                from kokoro_onnx import Kokoro
                self._kokoro = Kokoro(self.model_file, self.voices_file)
                self.cloner.set_kokoro(self._kokoro)
                return
            except Exception:
                pass

        try:
            import win32com.client
            self._fallback_sapi = win32com.client.Dispatch("SAPI.SpVoice")
        except Exception:
            pass

    def _synthesis_worker(self):
        """Genera el audio en segundo plano tan pronto llega el texto.
        
        De esta forma, la siguiente frase ya está calculada en RAM mientras la actual suena.
        """
        while self._is_running:
            text = self.text_queue.get()
            if text is None:
                self.audio_queue.put(None)
                break

            if not self.enabled or not text.strip():
                self.text_queue.task_done()
                continue

            try:
                self._init_tts()
                if self._kokoro is not None:
                    # Resolver si es una voz estándar o un perfil clonado/mezclado
                    active_style = self.cloner.resolve_voice(self.voice)
                    
                    # Generar audio
                    samples, sample_rate = self._kokoro.create(
                        text,
                        voice=active_style,
                        speed=self.speed,
                        lang=self.lang
                    )
                    # Recortar silencios innecesarios de inicio y fin (elimina pausas en ¡! y puntos)
                    trimmed = trim_audio_silence(samples, sample_rate, threshold=0.015, keep_leading_ms=20, keep_trailing_ms=70)
                    self.audio_queue.put((trimmed, sample_rate))
                elif self._fallback_sapi is not None:
                    # En fallback SAPI reproducimos directo
                    self._fallback_sapi.Speak(text)
            except Exception:
                pass
            finally:
                self.text_queue.task_done()

    def _playback_worker(self):
        """Reproduce inmediatamente el audio pre-sintetizado sin pausas entre oraciones."""
        import sounddevice as sd
        while self._is_running:
            item = self.audio_queue.get()
            if item is None:
                break
            
            samples, sample_rate = item
            try:
                sd.play(samples, sample_rate)
                sd.wait()
            except Exception:
                pass
            finally:
                self.audio_queue.task_done()

    def speak(self, text: str):
        """Añade una frase a la cola para ser sintetizada."""
        cleaned = clean_speech_text(text)
        if self.enabled and cleaned:
            self.text_queue.put(cleaned)

    def set_voice(self, voice_name: str):
        """Cambia la voz activa (ej: 'ef_dora', 'em_alex', o una voz personalizada de 'voices/')."""
        self.voice = voice_name

    def blend_voice(self, voice_weights: dict, output_name: str):
        """Crea una nueva voz mezclada y la establece como la voz activa."""
        self._init_tts()
        ok, msg = self.cloner.blend_voices(voice_weights, output_name)
        if ok:
            self.voice = output_name
        return ok, msg

    def list_custom_voices(self):
        """Lista las voces guardadas en 'voices/'."""
        return self.cloner.list_custom_voices()

    def set_speed(self, speed: float):
        """Ajusta la velocidad de habla (ej: 0.9, 0.95, 1.0, 1.1)."""
        self.speed = max(0.5, min(2.0, speed))

    def toggle(self) -> bool:
        """Activa o desactiva la voz del asistente."""
        self.enabled = not self.enabled
        return self.enabled

    def stop(self):
        """Detiene los hilos de síntesis y reproducción."""
        self._is_running = False
        self.text_queue.put(None)
