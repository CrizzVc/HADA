# ✨ HADA - Asistente de IA Local para PC

HADA es un asistente de inteligencia artificial personal, privado y ligero que se ejecuta 100% de manera local en tu ordenador. Permite interactuar mediante **texto escrito y voz**, además de realizar acciones en tu sistema mediante *Function Calling*.

---

## 🛠️ Tecnologías utilizadas

* **LLM (Cerebro)**: [Ollama](https://ollama.com/) (soporta modelos como `llama3.2:3b`, `llama3.2:1b`, `qwen2.5:3b`, `qwen2.5:1.5b`).
* **STT (Reconocimiento de Voz)**: [Vosk](https://alphacephei.com/vosk/) con el modelo ligero en español `vosk-model-small-es-0.42` (~45 MB).
* **TTS (Síntesis de Voz)**: [Kokoro-ONNX](https://github.com/thewh1teagle/kokoro-onnx), ultra natural, ligero (~300 MB) y compatible con Python 3.12, 3.13 y 3.14.
* **Acciones / Automatización de PC**: Control multimedia (Spotify, pausar/reproducir), clima en tiempo real, búsquedas en Google y apertura/cierre de programas en Windows.

---

## 📁 Estructura del proyecto

```text
HADA/
├── config.py              # Ajustes de modelos, voz y rutas
├── main.py                # Interfaz principal (texto + voz)
├── requirements.txt       # Dependencias de Python
├── core/
│   ├── assistant.py       # Conexión con Ollama y llamada a herramientas
│   └── prompt.py          # Instrucciones y personalidad de Hada
├── audio/
│   ├── listener.py        # Captura de micrófono con Vosk (STT)
│   └── speaker.py         # Síntesis de voz con Kokoro-ONNX (TTS)
├── tools/
│   ├── manager.py         # Registro de herramientas para Ollama
│   ├── media_tools.py     # Spotify y control de volumen/música
│   ├── system_tools.py    # Abrir y cerrar aplicaciones de Windows
│   └── web_tools.py       # Clima (Open-Meteo) y búsquedas web
└── models/
    ├── vosk/              # Descomprimir aquí el modelo de Vosk
    └── kokoro/            # kokoro-v1.0.onnx y voices-v1.0.bin
```

---

## 🚀 Instalación y Puesta en Marcha

### 1. Iniciar Ollama y descargar modelo
Asegúrate de tener [Ollama](https://ollama.com/) corriendo y descarga un modelo ligero:
```bash
ollama run llama3.2
```

### 2. Instalar dependencias
Con tu entorno virtual activo:
```bash
pip install -r requirements.txt
```

### 3. Descargar modelos ligeros

#### A. Modelo de Voz en Español de Vosk (STT)
1. Descarga [vosk-model-small-es-0.42.zip](https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip) (~45 MB).
2. Descomprímelo en `models/vosk/` de forma que quede:
   `models/vosk/vosk-model-small-es-0.42/`

#### B. Modelo de Kokoro-82M ONNX (TTS)
Descarga los dos archivos desde [Kokoro-ONNX Releases](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0):
* `kokoro-v1.0.onnx` (~300 MB)
* `voices-v1.0.bin` (~25 MB)

Guárdalos directamente dentro de la carpeta `models/kokoro/`.

---

## 💬 Cómo usar HADA

Inicia el asistente:
```bash
python main.py
```

### Comandos disponibles:
* **Escribir**: Escribe cualquier pregunta o petición y presiona `Enter`.
* **Hablar por voz**: Escribe `/mic` o presiona `Enter` con la línea vacía para activar el micrófono.
* **Activar/Desactivar voz de Hada**: `/voz`
* **Ver voces disponibles**: `/voces`
* **Cambiar de voz**: `/voz_estilo <nombre>`
* **Clonar / Crear voz híbrida**: `/clonar_mezcla <nombre> <voz1:peso> <voz2:peso>`
  *(Ejemplo: `/clonar_mezcla hada_dulce ef_dora:0.7 af_bella:0.3`)*
* **Grabar muestra de micrófono**: `/grabar_voz [segundos]`
* **Ajustar velocidad**: `/velocidad 0.95`
* **Cambiar modelo Ollama**: `/modelo [nombre]`
* **Reiniciar conversación**: `/limpiar`
* **Salir**: `/salir`

---

## 🎭 Clonación y Personalización de Voces

HADA cuenta con un motor de clonación y personalización en `voices/`:

1. **Clonar a partir de un archivo de audio (.wav, .mp3, .ogg, .flac)**:
   Coloca tu archivo en la carpeta `voices/` (o pasa la ruta completa) y ejecútalo:
   ```text
   /clonar_audio mi_voz.wav
   /clonar_audio "C:/audios/actor.mp3" voz_actor
   ```
   HADA analizará el tono, timbre y brillo de tu archivo y creará el perfil `.npy` en segundos.

2. **Crear una voz híbrida única (Voice Blending)**:
   Puedes mezclar proporciones de timbres existentes para dar con la personalidad exacta que buscas:
   ```text
   /clonar_mezcla mi_hada ef_dora:0.65 af_bella:0.35
   ```
   Esto genera un archivo `voices/mi_hada.npy` que puedes reutilizar siempre que quieras con `/voz_estilo mi_hada`.

3. **Cargar voces externas de la comunidad**:
   Cualquier archivo de voz de Kokoro en formato `.npy` o `.json` puede colocarse dentro de la carpeta `voices/` y activarse al instante.

4. **Grabar tu propia voz como referencia**:
   ```text
   /grabar_voz 5
   ```
   Graba 5 segundos limpios desde tu micrófono y los guarda en `voices/mi_voz_referencia.wav`.

### Ejemplos de acciones:
* *"Pausa la música"* o *"Siguiente canción"*
* *"Pon Queen en Spotify"*
* *"¿Qué tiempo hace en Madrid?"*
* *"Abre la calculadora"* o *"Abre el bloc de notas"*
* *"Busca recetas de paella en Google"*
