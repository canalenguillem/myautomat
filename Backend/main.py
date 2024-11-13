import argparse
from classes.YouTube import YouTube
from classes.Audio import Audio  # Suponiendo que la clase Audio está en classes/Audio.py

def main():
    # Configuración de los argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Descargar y transcribir videos de YouTube o transcribir un archivo de audio MP3.")
    parser.add_argument("--url", type=str, help="URL del video de YouTube")
    parser.add_argument("--audio", type=str, help="Ruta del archivo MP3 para transcribir")

    args = parser.parse_args()

    if args.url:
        # Si se proporciona la URL, realizar acciones con YouTube
        yt = YouTube(url=args.url)
        yt.descargar_mp3()
        yt.descargar_video()
        yt.transcribir_audio()
        yt.descargar_thumbnail()
        resultado = yt.generara_resumen_video()
        print(f"El resumen del video es:\n{resultado}")
        
    elif args.audio:
        # Si se proporciona el archivo MP3, transcribirlo usando la clase Audio
        audio = Audio(path_mp3=args.audio)
        transcripcion = audio.transcribe()
        # print(f"Transcripción:\n{transcripcion}")

        # Generar resumen de la transcripción
        resumen = audio.get_summary()
        print(f"Resumen:\n{resumen}")

    else:
        print("Debes proporcionar la URL del video de YouTube con --url o la ruta del archivo MP3 con --audio.")

if __name__ == "__main__":
    main()
