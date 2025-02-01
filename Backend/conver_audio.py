import argparse
from pydub import AudioSegment
import os

def convert_to_mp3(audio_path):
    """
    Convierte un archivo de audio .m4a a .mp3.

    Args:
        audio_path (str): Ruta del archivo de entrada en formato .m4a.

    Returns:
        str: Ruta del archivo convertido en formato .mp3.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"El archivo {audio_path} no existe.")

    if not audio_path.lower().endswith('.m4a'):
        raise ValueError("El archivo de entrada debe tener extensión .m4a.")

    # Definir la ruta de salida cambiando la extensión a .mp3
    mp3_path = os.path.splitext(audio_path)[0] + '.mp3'

    try:
        # Cargar el archivo de audio .m4a
        audio = AudioSegment.from_file(audio_path, format="m4a")
        # Exportar el archivo como .mp3
        audio.export(mp3_path, format="mp3")
        print(f"Conversión completada: {mp3_path}")
        return mp3_path
    except Exception as e:
        raise RuntimeError(f"Error al convertir el archivo: {e}")

def main():
    parser = argparse.ArgumentParser(description="Convierte un archivo de audio .m4a a .mp3.")
    parser.add_argument("--file", required=True, help="Ruta del archivo .m4a a convertir.")

    args = parser.parse_args()

    input_audio = args.file
    try:
        mp3_file = convert_to_mp3(input_audio)
        print(f"Archivo MP3 generado en: {mp3_file}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
