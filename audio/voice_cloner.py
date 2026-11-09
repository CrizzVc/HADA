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

        # Comprobar si es un archivo .npy en voices/
        npy_path = self.voices_dir / f"{target}.npy"
        if not npy_path.exists():
            npy_path = Path(target)

        if npy_path.exists() and npy_path.suffix == ".npy":
            try:
                arr = np.load(str(npy_path))
                return arr.astype(np.float32)
            except Exception as e:
                print(f"Error cargando voz .npy: {e}")

        # Comprobar si es un archivo .json de voz
        json_path = self.voices_dir / f"{target}.json"
        if not json_path.exists():
            json_path = Path(target)
        if json_path.exists() and json_path.suffix == ".json":
            try:
                with open(json_path, "r", encoding="utf-8") as f:
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
