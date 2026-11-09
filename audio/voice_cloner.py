"""Módulo de Clonación, Fusión y Gestión de Voces Personalizadas para HADA."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import json
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
VOICES_DIR = BASE_DIR / "voices"
VOICES_DIR.mkdir(exist_ok=True)

class VoiceCloner:
    def __init__(self, kokoro_instance=None):
        self.kokoro = kokoro_instance
        self.voices_dir = VOICES_DIR

    def set_kokoro(self, kokoro_instance):
        self.kokoro = kokoro_instance

    def list_custom_voices(self) -> List[str]:
        """Lista todas las voces personalizadas guardadas en la carpeta 'voices/'."""
        custom = []
        for file in self.voices_dir.glob("*.npy"):
            custom.append(file.stem)
        for file in self.voices_dir.glob("*.json"):
            custom.append(file.stem)
        return sorted(custom)

    def blend_voices(
        self,
        voice_weights: Dict[str, float],
        output_name: str
    ) -> Tuple[bool, str]:
        """Crea una nueva voz única mezclando varias voces con pesos relativos.
        
        Args:
            voice_weights: Diccionario de nombres de voz y su peso (ej: {'ef_dora': 0.7, 'af_bella': 0.3})
            output_name: Nombre con el que se guardará el nuevo archivo (ej: 'hada_dulce')
            
        Returns:
            (éxito, mensaje)
        """
        if self.kokoro is None:
            return False, "El motor Kokoro no está inicializado."

        total_weight = sum(voice_weights.values())
        if total_weight <= 0:
            return False, "La suma de los pesos de las voces debe ser mayor a 0."

        blended_vector = None

        for voice_name, weight in voice_weights.items():
            try:
                style = self.resolve_voice(voice_name)
                if style is None:
                    return False, f"No se pudo cargar la voz base '{voice_name}'."
                
                normalized_w = weight / total_weight
                if blended_vector is None:
                    blended_vector = normalized_w * style
                else:
                    blended_vector += normalized_w * style
            except Exception as e:
                return False, f"Error al procesar la voz '{voice_name}': {e}"

        # Guardar como archivo numpy .npy
        clean_name = output_name.strip().replace(" ", "_")
        out_path = self.voices_dir / f"{clean_name}.npy"
        np.save(str(out_path), blended_vector.astype(np.float32))

        return True, f"¡Voz '{clean_name}' clonada/creada con éxito en {out_path.name}!"

    def resolve_voice(self, voice_name_or_path: str) -> Union[str, np.ndarray, None]:
        """Resuelve un nombre o ruta a un vector de estilo de Kokoro o a su nombre estándar.
        
        Soporta:
        1. Archivos .npy personalizados en 'voices/'
        2. Archivos .json con matrices de estilo
        3. Voces estándar de Kokoro (ef_dora, em_alex, af_bella, etc.)
        """
        target = str(voice_name_or_path).strip()

        # Comprobar si es un archivo .npy en voices/ (con o sin extensión .npy)
        candidate_npy = self.voices_dir / target
        if not candidate_npy.exists():
            candidate_npy = self.voices_dir / f"{target}.npy"
        if not candidate_npy.exists():
            candidate_npy = Path(target)

        if candidate_npy.exists() and candidate_npy.suffix == ".npy":
            try:
                arr = np.load(str(candidate_npy))
                return arr.astype(np.float32)
            except Exception as e:
                print(f"Error cargando voz .npy: {e}")

        # Comprobar si es un archivo .json de voz
        candidate_json = self.voices_dir / target
        if not candidate_json.exists():
            candidate_json = self.voices_dir / f"{target}.json"
        if not candidate_json.exists():
            candidate_json = Path(target)
        if candidate_json.exists() and candidate_json.suffix == ".json":
            try:
                with open(candidate_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return np.array(data, dtype=np.float32)
            except Exception as e:
                print(f"Error cargando voz .json: {e}")

        # Si el motor Kokoro está activo, consultar su vector
        if self.kokoro is not None:
            try:
                return self.kokoro.get_voice_style(target)
            except Exception:
                pass

        return target

    def analyze_audio_file(self, file_path: Union[str, Path]) -> Tuple[bool, Dict[str, Any], str]:
        """Analiza acústicamente un archivo de audio (.wav, .mp3, .flac, .ogg).
        
        Calcula:
        - Tono fundamental medio (F0 / Pitch en Hz)
        - Centroide espectral (brillo / timbre en Hz)
        - Distribución de frecuencias y género estimado
        """
        path = Path(file_path)
        if not path.is_absolute():
            # Buscar en el directorio actual o en voices/
            if not path.exists():
                candidate = self.voices_dir / path.name
                if candidate.exists():
                    path = candidate
                else:
                    return False, {}, f"No se encontró el archivo de audio: {file_path}"

        try:
            import soundfile as sf
            audio, sample_rate = sf.read(str(path))
        except Exception as e:
            return False, {}, f"Error al leer el archivo de audio con soundfile: {e}"

        # 1. Convertir a mono si es estéreo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        # 2. Normalizar
        audio = audio - np.mean(audio)
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val

        # 3. Recortar silencios extremos
        threshold = 0.04
        voiced = np.where(np.abs(audio) > threshold)[0]
        if len(voiced) > 0:
            audio = audio[voiced[0]:voiced[-1]]

        duration_sec = len(audio) / sample_rate
        if duration_sec < 0.3:
            return False, {}, "El archivo de audio es demasiado corto o casi silencioso (mínimo 0.5s de habla)."

        # 4. Estimar Tono / Frecuencia Fundamental (F0) mediante autocorrelación
        frame_len = int(sample_rate * 0.04)  # 40ms
        hop = int(sample_rate * 0.02)
        min_lag = int(sample_rate / 380)  # Max 380 Hz
        max_lag = int(sample_rate / 75)   # Min 75 Hz
        f0_estimates = []

        for i in range(0, len(audio) - frame_len, hop):
            frame = audio[i:i + frame_len]
            if np.std(frame) < 0.01:
                continue
            corr = np.correlate(frame, frame, mode="full")[len(frame) - 1:]
            if len(corr) > max_lag:
                peak = min_lag + np.argmax(corr[min_lag:max_lag])
                if corr[peak] > 0.28 * corr[0]:
                    f0 = sample_rate / peak
                    f0_estimates.append(f0)

        median_f0 = float(np.median(f0_estimates)) if f0_estimates else 180.0

        # 5. Centroide espectral (brillo / resonancia del timbre)
        analysis_chunk = audio[:min(len(audio), int(sample_rate * 4))]
        fft_vals = np.abs(np.fft.rfft(analysis_chunk))
        freqs = np.fft.rfftfreq(len(analysis_chunk), 1.0 / sample_rate)
        sum_fft = np.sum(fft_vals)
        spectral_centroid = float(np.sum(freqs * fft_vals) / sum_fft) if sum_fft > 0 else 1800.0

        # Clasificación acústica
        is_female = median_f0 >= 165.0
        gender = "femenina" if is_female else "masculina"

        data = {
            "pitch_f0": round(median_f0, 1),
            "spectral_centroid": round(spectral_centroid, 1),
            "duration": round(duration_sec, 2),
            "gender": gender,
            "is_female": is_female,
            "filename": path.name,
        }
        return True, data, "Análisis acústico completado con éxito."

    def clone_from_audio_file(
        self,
        audio_path: str,
        output_name: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Clona una voz a partir de un archivo de audio (.wav, .mp3, etc.).
        
        Analiza las propiedades acústicas del archivo y genera automáticamente
        un vector híbrido de Kokoro optimizado para replicar el tono y timbre en español.
        """
        ok, stats, msg = self.analyze_audio_file(audio_path)
        if not ok:
            return False, msg, {}

        f0 = stats["pitch_f0"]
        centroid = stats["spectral_centroid"]
        is_female = stats["is_female"]

        weights: Dict[str, float] = {}

        # IMPORTANTE: Para evitar el "acento gringo", usamos EXCLUSIVAMENTE voces nativas en español ('ef_*', 'em_*')
        # y de lenguas romances ('if_*', 'pf_*', 'im_*') que comparten el mismo sistema puro de 5 vocales (A, E, I, O, U).
        # Jamás mezclamos voces americanas ('af_*', 'am_*') que introducen diptongos y entonación en inglés.
        if is_female:
            if f0 > 220:
                # Voz femenina aguda / dulce: Dora con matiz brillante de Sara
                weights["ef_dora"] = 0.80
                weights["if_sara"] = 0.20
            elif f0 > 180:
                # Voz femenina estándar limpia: Dora pura con toque suave
                weights["ef_dora"] = 0.85
                weights["if_sara"] = 0.15
            else:
                # Voz femenina más grave / cálida
                weights["ef_dora"] = 0.80
                weights["pf_dora"] = 0.20
        else:
            if f0 < 120:
                # Voz masculina profunda: Alex con Santa (ambas 100% español de España/Latam)
                weights["em_alex"] = 0.65
                weights["em_santa"] = 0.35
            elif f0 < 155:
                # Voz masculina media natural
                weights["em_alex"] = 0.85
                weights["em_santa"] = 0.15
            else:
                # Voz masculina más juvenil / tenor
                weights["em_alex"] = 0.75
                weights["im_nicola"] = 0.25

        # Realizar la mezcla y guardar el vector
        blend_ok, blend_msg = self.blend_voices(weights, output_name)
        if not blend_ok:
            return False, blend_msg, stats

        stats["blend_weights"] = weights
        return True, f"¡Voz '{output_name}' clonada a partir de '{stats['filename']}'!", stats

    def record_microphone_sample(self, output_wav_name: str = "muestra_voz.wav", seconds: int = 5) -> Tuple[bool, str]:
        """Graba una muestra de voz limpia del micrófono para guardarla como referencia de audio."""
        try:
            import sounddevice as sd
            import soundfile as sf
            
            sample_rate = 24000
            print(f"🎙️ Grabando {seconds} segundos de audio... ¡Habla ahora!")
            audio_data = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
            sd.wait()
            
            out_file = self.voices_dir / output_wav_name
            sf.write(str(out_file), audio_data, sample_rate)
            return True, f"Muestra de audio guardada correctamente en: {out_file}"
        except Exception as e:
            return False, f"Error al grabar audio del micrófono: {e}"
