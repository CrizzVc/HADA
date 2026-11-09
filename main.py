"""Punto de entrada principal para HADA: Asistente local con texto, voz y herramientas."""
import sys
from audio.listener import VoskListener
from audio.speaker import KokoroSpeaker
from config import ASSISTANT_NAME, DEFAULT_MODEL, VOSK_MODEL_PATH
from core.assistant import HadaAssistant

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    console = Console()
except ImportError:
    # Fallback básico si rich aún no está instalado
    class SimpleConsole:
        def print(self, *args, **kwargs):
            print(*args)
    console = SimpleConsole()

def print_banner(ollama_status: str, vosk_ready: bool, speaker_enabled: bool):
    banner = f"""[bold magenta]════════════════════════════════════════════════════════════[/bold magenta]
[bold cyan] ✨ {ASSISTANT_NAME.upper()} - Asistente Local de IA para tu PC ✨ [/bold cyan]
[bold magenta]════════════════════════════════════════════════════════════[/bold magenta]
• [bold]Ollama:[/bold] {ollama_status}
• [bold]Micrófono (Vosk):[/bold] {'[green]Listo[/green]' if vosk_ready else '[yellow]Modelo no encontrado (usa texto o descarga vosk-model-small-es)[/yellow]'}
• [bold]Voz de salida (Kokoro):[/bold] {'[green]Activada[/green]' if speaker_enabled else '[red]Desactivada[/red]'}

[bold yellow]Comandos rápidos:[/bold yellow]
• Escribe tu mensaje y presiona [bold]Enter[/bold] para chatear.
• Escribe [bold]/mic[/bold] (o pulsa Enter vacío) para hablar por el micrófono.
• Escribe [bold]/voz[/bold] para alternar la voz de Hada (on/off).
• Escribe [bold]/limpiar[/bold] para reiniciar la memoria del chat.
• Escribe [bold]/salir[/bold] para cerrar el asistente.
[bold magenta]════════════════════════════════════════════════════════════[/bold magenta]"""
    console.print(banner)

def main():
    assistant = HadaAssistant(model=DEFAULT_MODEL)
    speaker = KokoroSpeaker()
    listener = VoskListener()

    # Verificar estado de conexión con Ollama
    is_connected, status_msg = assistant.check_connection()
    vosk_ready = listener.is_model_available()

    print_banner(status_msg, vosk_ready, speaker.enabled)

    if not is_connected:
        console.print(
            f"\n[bold red][!] Advertencia:[/bold red] {status_msg}\n"
            "[yellow]Puedes iniciar Ollama y seguir usando HADA sin reiniciar este programa.[/yellow]\n"
        )

    while True:
        try:
            user_input = input(f"\nTú > ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold cyan]¡Hasta luego![/bold cyan]")
            speaker.stop()
            break

        if not user_input or user_input.lower() == "/mic":
            # Modo micrófono
            if not listener.is_model_available():
                console.print(
                    f"[yellow][!] El modelo de Vosk no se encuentra en:\n    {VOSK_MODEL_PATH}\n"
                    "Descarga 'vosk-model-small-es-0.42' desde https://alphacephei.com/vosk/models y descomprímelo ahí.[/yellow]"
                )
                continue
            
            console.print("[bold red]🎙️ Escuchando... (habla ahora)[/bold red]")
            user_input = listener.listen_once()
            if not user_input:
                console.print("[dim]No se detectó ninguna voz o no se entendió.[/dim]")
                continue
            console.print(f"[bold cyan]Tú (voz) >[/bold cyan] {user_input}")

        # Comandos de control
        cmd = user_input.lower()
        if cmd in ["/salir", "salir", "exit", "quit"]:
            console.print("[bold cyan]¡Hasta pronto![/bold cyan]")
            speaker.stop()
            break
        elif cmd == "/voz":
            current = speaker.toggle()
            state = "activada" if current else "desactivada"
            console.print(f"[magenta]Voz del asistente {state}.[/magenta]")
            continue
        elif cmd == "/limpiar":
            assistant.reset_chat()
            console.print("[green]Memoria de conversación reiniciada.[/green]")
            continue
        elif cmd.startswith("/modelo"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                new_model = parts[1].strip()
                assistant.model = new_model
                console.print(f"[green]Modelo cambiado a: {new_model}[/green]")
            else:
                _, status = assistant.check_connection()
                console.print(status)
            continue
        elif cmd.startswith("/voz_estilo"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                new_voice = parts[1].strip()
                speaker.set_voice(new_voice)
                console.print(f"[green]Voz cambiada a: {new_voice} (ej: ef_dora, em_alex, em_santa)[/green]")
            else:
                console.print(f"[magenta]Voz actual: {speaker.voice}. Voces recomendadas: ef_dora (femenina), em_alex (masculina), em_santa (masculina).[/magenta]")
            continue
        elif cmd.startswith("/velocidad"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                try:
                    spd = float(parts[1].strip())
                    speaker.set_speed(spd)
                    console.print(f"[green]Velocidad de habla ajustada a: {spd}[/green]")
                except ValueError:
                    console.print("[red]Uso: /velocidad 0.95[/red]")
            else:
                console.print(f"[magenta]Velocidad actual: {speaker.speed} (Recomendado: 0.9 a 1.0)[/magenta]")
            continue
        elif cmd == "/ayuda":
            console.print(
                "[cyan]Comandos:\n"
                "  /mic                - Hablar por micrófono\n"
                "  /voz                - Activar/Desactivar voz de Hada\n"
                "  /voz_estilo [voz]   - Cambiar voz (ef_dora, em_alex, etc.)\n"
                "  /velocidad [valor]  - Ajustar velocidad (ej: 0.95, 1.0)\n"
                "  /modelo [nombre]    - Ver o cambiar el modelo de Ollama\n"
                "  /limpiar            - Reiniciar conversación\n"
                "  /salir              - Salir[/cyan]"
            )
            continue

        # Enviar al asistente y procesar respuesta con streaming
        print(f"\n{ASSISTANT_NAME} > ", end="", flush=True)
        try:
            for token, complete_sentence in assistant.chat_stream(user_input):
                if token:
                    print(token, end="", flush=True)
                if complete_sentence:
                    speaker.speak(complete_sentence)
            print()  # Salto de línea al terminar
        except Exception as e:
            console.print(f"\n[red]Error al procesar respuesta: {e}[/red]")

if __name__ == "__main__":
    main()

