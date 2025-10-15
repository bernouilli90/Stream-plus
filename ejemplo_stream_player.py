#!/usr/bin/env python3
"""
Ejemplos de uso del Reproductor de Streams Alternativo

Este archivo demuestra todas las funcionalidades disponibles:
- Acceso con URLs con credenciales (para VLC)
- Proxy autenticado (para ffmpeg)
- Procesamiento directo con ffmpeg
- Pruebas de conexión
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stream_player import StreamPlayer

def ejemplo_basico():
    """Ejemplo básico de uso"""
    print("=== EJEMPLO BÁSICO ===")

    # Crear reproductor con credenciales
    player = StreamPlayer(
        base_url="http://localhost:5000",
        username="admin",
        password="tu_password"
    )

    # Obtener URL del proxy para usar con ffmpeg
    proxy_url = player.get_proxy_stream_url(123)
    print(f"URL del proxy: {proxy_url}")

    # Probar conexión
    success = player.test_proxy_connection(123)
    print(f"Conexión al proxy: {'OK' if success else 'ERROR'}")

def ejemplo_ffmpeg():
    """Ejemplo de procesamiento con ffmpeg"""
    print("\n=== EJEMPLO FFMPEG ===")

    player = StreamPlayer(
        base_url="http://localhost:5000",
        username="admin",
        password="tu_password"
    )

    # Procesar stream con ffmpeg (comando por defecto)
    success = player.stream_to_ffmpeg(123)
    print(f"Procesamiento con ffmpeg: {'OK' if success else 'ERROR'}")

    # Procesar con comando personalizado
    custom_command = "ffmpeg -i {url} -f null -"
    success = player.stream_to_ffmpeg(123, command=custom_command)
    print(f"Procesamiento personalizado: {'OK' if success else 'ERROR'}")

def ejemplo_linea_comandos():
    """Ejemplos de uso desde línea de comandos"""
    print("\n=== EJEMPLOS DE LÍNEA DE COMANDOS ===")

    print("# Obtener URL del proxy para usar con ffmpeg:")
    print("python stream_player.py http://localhost:5000 123 admin password --proxy")
    print()

    print("# Probar conexión al proxy:")
    print("python stream_player.py http://localhost:5000 123 admin password --test")
    print()

    print("# Procesar con ffmpeg:")
    print("python stream_player.py http://localhost:5000 123 admin password --ffmpeg")
    print()

    print("# Usar con VLC (URLs con credenciales):")
    print("python stream_player.py http://localhost:5000 123 admin password")
    print()

    print("# Usar endpoint /live/:")
    print("python stream_player.py http://localhost:5000 123 admin password --live")
    print()

    print("# Listar streams disponibles:")
    print("python stream_player.py http://localhost:5000 list admin password")

def ejemplo_avanzado():
    """Ejemplo avanzado con manejo de errores"""
    print("\n=== EJEMPLO AVANZADO ===")

    player = StreamPlayer(
        base_url="http://localhost:5000",
        username="admin",
        password="tu_password"
    )

    try:
        # Obtener información del stream
        info = player.get_stream_info(123)
        print(f"Información del stream: {info}")

        # Encontrar canal que contiene el stream
        channel = player.find_channel_by_stream(123)
        print(f"Canal encontrado: {channel}")

        # Acceso completo con todas las opciones
        print("\nProbando todas las opciones de acceso:")

        # URLs con credenciales (para VLC)
        success = player.play_stream_by_id(123, use_vlc=False, use_live=False, use_proxy=False)
        print(f"URLs con credenciales: {'OK' if success else 'ERROR'}")

        # Proxy autenticado
        success = player.play_stream_by_id(123, use_vlc=False, use_live=False, use_proxy=True)
        print(f"Proxy autenticado: {'OK' if success else 'ERROR'}")

    except Exception as e:
        print(f"Error en ejemplo avanzado: {e}")

def ejemplo_ffmpeg_externo():
    """Ejemplos de uso con ffmpeg externo"""
    print("\n=== EJEMPLO FFMPEG EXTERNO ===")

    print("# 1. Obtener URL del proxy y usarla con ffmpeg:")
    print('PROXY_URL=$(python stream_player.py http://localhost:5000 123 admin password --proxy)')
    print('ffmpeg -i "$PROXY_URL" -f null -')
    print()

    print("# 2. Ver información del stream:")
    print('ffmpeg -i "$(python stream_player.py http://localhost:5000 123 admin password --proxy)" -f null -')
    print()

    print("# 3. Convertir a archivo MP4:")
    print('ffmpeg -i "$(python stream_player.py http://localhost:5000 123 admin password --proxy)" -c copy output.mp4')
    print()

    print("# 4. Transmitir a RTMP:")
    print('ffmpeg -i "$(python stream_player.py http://localhost:5000 123 admin password --proxy)" -f flv rtmp://destino/stream')
    print()

    print("# 5. Extraer audio:")
    print('ffmpeg -i "$(python stream_player.py http://localhost:5000 123 admin password --proxy)" -vn -acodec copy audio.aac')

if __name__ == "__main__":
    print("EJEMPLOS DE USO DEL REPRODUCTOR DE STREAMS ALTERNATIVO")
    print("=" * 60)

    # Verificar que stream_player.py existe
    if not os.path.exists("stream_player.py"):
        print("ERROR: stream_player.py no encontrado. Ejecuta primero el script principal.")
        sys.exit(1)

    ejemplo_basico()
    ejemplo_ffmpeg()
    ejemplo_linea_comandos()
    ejemplo_avanzado()
    ejemplo_ffmpeg_externo()

    print("\n" + "=" * 60)
    print("¡Todos los ejemplos completados!")
    print("Recuerda configurar las credenciales correctas para tu instalación de Dispatcharr.")