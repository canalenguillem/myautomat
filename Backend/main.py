import argparse
from classes.YouTube import YouTube

def main():
    # Configuración de los argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Descargar y transcribir videos de YouTube.")
    parser.add_argument("--url", type=str, required=True, help="URL del video de YouTube")
    args = parser.parse_args()

    # Crear instancia de YouTube con la URL proporcionada
    yt = YouTube(url=args.url)
    yt.descargar_mp3()
    yt.descargar_video()
    yt.transcribir_audio()
    yt.descargar_thumbnail()
    # resultado=yt.generar_articulo_blog()
    # print(f"El artículo generado es:\n{resultado}")
    resultado=yt.generara_resumen_video()
    print(f"El artículo generado es:\n{resultado}")

if __name__ == "__main__":
    main()
