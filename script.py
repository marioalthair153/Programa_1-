import requests
from bs4 import BeautifulSoup
import pyttsx3
import os
from moviepy.editor import *
import random
from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity
from skimage.color import rgb2gray

# Función para realizar una búsqueda en YouTube
def buscar_en_youtube(query):
    response = requests.get(f"https://www.youtube.com/results?search_query={query}")
    soup = BeautifulSoup(response.text, "html.parser")
    resultados = soup.select("a#video-title")
    random.shuffle(resultados)
    resultados = resultados[:5]
    titulos = [resultado.text for resultado in resultados]
    return titulos

# Función para realizar una búsqueda en Google
def buscar_en_google(tema):
    response = requests.get(f"https://www.google.com/search?q={tema}")
    soup = BeautifulSoup(response.text, "html.parser")
    resultados = soup.select(".kCrYT a")
    titulos = [resultado.text for resultado in resultados[:10]]
    return titulos

# Función para generar el guion del video
def generar_guion(tema):
    query = f"{tema} explicación"
    youtube_results = buscar_en_youtube(query)
    google_results = buscar_en_google(tema)
    resultados = youtube_results + google_results
    guion = "\n".join(resultados)
    return guion

# Función para generar la voz en off
def generar_voz_en_off(guion):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    audio_path = "audio.mp3"
    engine.save_to_file(guion, audio_path)
    engine.runAndWait()
    return audio_path

# Función para seleccionar las mejores imágenes en lotes
def seleccionar_mejores_imagenes_en_lotes(carpeta_imagenes, lote_size):
    archivos_imagenes = os.listdir(carpeta_imagenes)
    archivos_imagenes = [archivo for archivo in archivos_imagenes if archivo.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    for i in range(0, len(archivos_imagenes), lote_size):
        yield archivos_imagenes[i:i + lote_size]

# Función para reducir la resolución de una imagen
def reducir_resolucion_imagen(imagen, resolucion):
    imagen_redimensionada = imagen.resize(resolucion)
    return imagen_redimensionada

# Función para eliminar imágenes parecidas
def eliminar_imagenes_parecidas(carpeta_imagenes, lote_size=10, umbral_similitud=0.9):
    archivos_imagenes = os.listdir(carpeta_imagenes)
    archivos_imagenes = [archivo for archivo in archivos_imagenes if archivo.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    imagenes_a_eliminar = set()
    for lote_imagenes in seleccionar_mejores_imagenes_en_lotes(carpeta_imagenes, lote_size):
        for i in range(len(lote_imagenes)):
            imagen_a_comparar = Image.open(os.path.join(carpeta_imagenes, lote_imagenes[i]))
            imagen_a_comparar_resized = reducir_resolucion_imagen(imagen_a_comparar, (100, 100))
            imagen_a_comparar_resized_grayscale = rgb2gray(np.array(imagen_a_comparar_resized))  # Convertir a escala de grises

            for j in range(i + 1, len(lote_imagenes)):
                imagen_actual = Image.open(os.path.join(carpeta_imagenes, lote_imagenes[j]))
                imagen_actual_resized = reducir_resolucion_imagen(imagen_actual, (100, 100))
                imagen_actual_resized_grayscale = rgb2gray(np.array(imagen_actual_resized))  # Convertir a escala de grises

                similitud = structural_similarity(imagen_a_comparar_resized_grayscale, imagen_actual_resized_grayscale)

                if similitud > umbral_similitud:
                    imagenes_a_eliminar.add(lote_imagenes[j])

                imagen_actual.close()
                imagen_actual_resized.close()

            imagen_a_comparar.close()
            imagen_a_comparar_resized.close()

    for imagen_a_eliminar in imagenes_a_eliminar:
        ruta_imagen_a_eliminar = os.path.join(carpeta_imagenes, imagen_a_eliminar)
        os.remove(ruta_imagen_a_eliminar)

# Función para crear el video final
def crear_video(guion, carpeta_imagenes, carpeta_videos, duracion, carpeta_destino, resolucion):
    clips = []
    lote_size = 50  # Tamaño del lote de imágenes a procesar
    generador_lotes = seleccionar_mejores_imagenes_en_lotes(carpeta_imagenes, lote_size)

    for lote_imagenes in generador_lotes:
        for archivo_imagen in lote_imagenes:
            imagen_original = Image.open(os.path.join(carpeta_imagenes, archivo_imagen))
            imagen_redimensionada = reducir_resolucion_imagen(imagen_original, resolucion)
            clip = ImageClip(np.array(imagen_redimensionada.copy())).set_duration(duracion)
            clips.append(clip)

            # Liberar memoria
            imagen_original.close()
            imagen_redimensionada.close()

    archivos_videos = os.listdir(carpeta_videos)
    archivos_videos = [archivo for archivo in archivos_videos if archivo.lower().endswith('.mp4')]
    for archivo_video in archivos_videos:
        clip = VideoFileClip(os.path.join(carpeta_videos, archivo_video)).subclip(0, duracion)
        clips.append(clip)

    video = concatenate_videoclips(clips)

    voz_en_off = generar_voz_en_off(guion)
    audio = AudioFileClip(voz_en_off)
    video = video.set_audio(audio)

    video_path = os.path.join(carpeta_destino, "video.mp4")
    video.write_videofile(video_path, codec="libx264", fps=24)  # Agregar el parámetro 'fps' con el valor deseado

    # Liberar recursos
    video.reader.close()
    video.audio.reader.close_proc()
    audio.reader.close_proc()

    return video_path

# Pedir al usuario los datos de entrada
tema = input("Ingrese el tema del video: ")
duracion = int(input("Ingrese la duración del video en minutos: "))
carpeta_destino = input("Ingrese la ruta de la carpeta para el video: ")

# Generar guion
guion = generar_guion(tema)

# Crear carpeta para imágenes
carpeta_imagenes = os.path.join(carpeta_destino, "imagenes")
os.makedirs(carpeta_imagenes, exist_ok=True)

# Eliminar imágenes parecidas
eliminar_imagenes_parecidas(carpeta_imagenes)

# Crear video final
carpeta_videos = "D:\\videos para subir en youtube\\videos explicativos canal de youtube\\imagenes de la pelicula\\Recortes del video"
resolucion = (1280, 720)  # Cambiar la resolución según tus preferencias
video_generado = crear_video(guion, carpeta_imagenes, carpeta_videos, duracion * 60, carpeta_destino, resolucion)

print("El video se ha generado correctamente.")
print("Ruta del video generado:", video_generado)