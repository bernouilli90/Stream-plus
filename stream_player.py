#!/usr/bin/env python3
"""
Script alternativo para reproducir streams específicos por ID
Sin modificar el código existente del cliente
"""

import requests
import json
import sys
import time
from typing import Dict, Optional, Any
import subprocess
import threading
import signal
import os

class StreamPlayer:
    """Clase alternativa para reproducir streams específicos por ID"""

    def __init__(self, base_url: str, username: str = None, password: str = None):
        """
        Inicializar el reproductor de streams
        Args:
            base_url: URL base de la API de Dispatcharr
            username: Usuario para autenticación
            password: Contraseña para autenticación
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token = None
        self.username = username
        self.password = password

        # Configurar headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        # Autenticar si se proporcionan credenciales
        if self.username and self.password:
            self.authenticate()

    def authenticate(self) -> bool:
        """Autenticar con la API usando JWT"""
        try:
            url = f"{self.base_url}/api/accounts/token/"
            data = {"username": self.username, "password": self.password}
            response = self.session.post(url, json=data)
            response.raise_for_status()

            result = response.json()
            token = result.get('access')
            if not token:
                print("❌ No se recibió token JWT")
                return False

            self.token = token
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
            print("✅ Autenticación exitosa")
            return True

        except Exception as e:
            print(f"❌ Error de autenticación: {e}")
            return False

    def get_stream_info(self, stream_id: int) -> Optional[Dict[str, Any]]:
        """Obtener información de un stream específico"""
        try:
            url = f"{self.base_url}/api/channels/streams/{stream_id}/"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error obteniendo información del stream {stream_id}: {e}")
            return None

    def find_channel_by_stream(self, stream_id: int) -> Optional[int]:
        """Buscar un canal que contenga el stream especificado"""
        try:
            # Obtener todos los canales con paginación
            page = 1
            while True:
                url = f"{self.base_url}/api/channels/channels/?page={page}&page_size=100"
                response = self.session.get(url)
                response.raise_for_status()
                data = response.json()

                # Buscar en los resultados
                for channel in data.get('results', []):
                    if stream_id in channel.get('streams', []):
                        return channel['id']

                # Verificar si hay más páginas
                if not data.get('next'):
                    break
                page += 1

            return None

        except Exception as e:
            print(f"❌ Error buscando canal para stream {stream_id}: {e}")
            return None

    def play_stream_by_id(self, stream_id: int, use_vlc: bool = True, use_live_endpoint: bool = False, use_proxy: bool = False) -> bool:
        """
        Acceder a un stream específico por ID
        Args:
            stream_id: ID del stream a acceder
            use_vlc: Si usar VLC para reproducción (True) o solo mostrar URL (False)
            use_live_endpoint: Si usar /live/ endpoint en lugar del estándar
            use_proxy: Si usar proxy autenticado (compatible con ffmpeg)
        """
        print(f"🎬 Intentando acceder a stream ID: {stream_id}")

        # Verificar que tengamos credenciales para los endpoints con auth en URL
        if not use_proxy and (not self.username or not self.password):
            print("❌ Se requieren credenciales (username y password) para acceder a streams")
            print("💡 Usa: StreamPlayer(base_url, username='tu_user', password='tu_pass')")
            return False

        # Obtener información del stream
        stream_info = self.get_stream_info(stream_id)
        if not stream_info:
            print("❌ No se pudo obtener información del stream")
            return False

        print(f"📋 Información del stream: {stream_info.get('name', 'Sin nombre')}")

        # Buscar canal que contenga este stream
        channel_id = self.find_channel_by_stream(stream_id)
        if not channel_id:
            print("❌ No se encontró un canal que contenga este stream")
            print("💡 Intentando acceso directo desde la URL del stream...")

            # Intentar acceso directo desde la URL del stream
            stream_url = stream_info.get('url')
            if stream_url:
                return self._play_url(stream_url, use_vlc)
            else:
                print("❌ El stream no tiene URL disponible")
                return False

        print(f"📺 Canal encontrado: {channel_id}")

        if use_proxy:
            # Usar proxy autenticado (compatible con ffmpeg)
            proxy_url = f"{self.base_url}/proxy/ts/stream/{channel_id}"
            print(f"🎯 Usando proxy autenticado: {proxy_url}")
            return self._play_proxy_url(proxy_url, use_vlc)
        else:
            # Usar endpoint con autenticación integrada en la URL
            if use_live_endpoint:
                stream_url = f"{self.base_url}/live/{self.username}/{self.password}/{channel_id}"
            else:
                stream_url = f"{self.base_url}/{self.username}/{self.password}/{channel_id}"

            print(f"🎯 URL de streaming: {stream_url}")
            return self._play_url(stream_url, use_vlc)

    def _play_proxy_url(self, proxy_url: str, use_vlc: bool = True) -> bool:
        """Acceder a una URL de proxy usando la sesión autenticada"""
        if not use_vlc:
            print(f"🔗 URL de proxy autenticado: {proxy_url}")
            print("💡 Usa esta URL con ffmpeg o curl con las cookies de sesión")
            return True

        try:
            # Para VLC, necesitamos una forma diferente ya que no puede usar sesiones HTTP
            # Por ahora, solo mostrar la URL
            print("⚠️  Para usar con VLC, usa URLs con credenciales en lugar de proxy")
            print(f"🔗 URL de proxy: {proxy_url}")
            print("💡 Recomendación: usa use_proxy=False para URLs con credenciales")
            return False

        except Exception as e:
            print(f"❌ Error accediendo al proxy: {e}")
            return False

    def get_proxy_stream_url(self, stream_id: int) -> Optional[str]:
        """
        Obtiene la URL del proxy para un stream específico
        Esta URL puede usarse directamente con ffmpeg
        """
        print(f"🔗 Obteniendo URL de proxy para stream ID: {stream_id}")

        # Buscar canal que contenga este stream
        channel_id = self.find_channel_by_stream(stream_id)
        if not channel_id:
            print("❌ No se encontró un canal que contenga este stream")
            return None

        # URL del proxy con autenticación Bearer
        proxy_url = f"{self.base_url}/proxy/ts/stream/{channel_id}"
        print(f"✅ URL de proxy obtenida: {proxy_url}")
        print("💡 Esta URL incluye autenticación Bearer automática")

        return proxy_url

    def stream_to_ffmpeg(self, stream_id: int, ffmpeg_command: str = None) -> bool:
        """
        Stream a un comando ffmpeg usando el proxy autenticado
        Args:
            stream_id: ID del stream a procesar
            ffmpeg_command: Comando ffmpeg personalizado (opcional)
        """
        proxy_url = self.get_proxy_stream_url(stream_id)
        if not proxy_url:
            return False

        if not ffmpeg_command:
            # Comando básico para verificar que funciona
            ffmpeg_command = 'ffmpeg -i - -f null -'

        print(f"🎬 Ejecutando ffmpeg con proxy: {ffmpeg_command}")

        try:
            # Hacer la petición al proxy
            response = self.session.get(proxy_url, stream=True)
            response.raise_for_status()

            # Ejecutar ffmpeg con el stream
            import subprocess
            process = subprocess.Popen(
                ffmpeg_command.split(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Enviar el stream a ffmpeg
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    process.stdin.write(chunk)
                    process.stdin.flush()

            process.stdin.close()
            process.wait()

            if process.returncode == 0:
                print("✅ ffmpeg procesó el stream exitosamente")
                return True
            else:
                print(f"❌ ffmpeg terminó con código: {process.returncode}")
                return False

        except Exception as e:
            print(f"❌ Error procesando stream con ffmpeg: {e}")
            return False

    def test_proxy_connection(self, stream_id: int) -> bool:
        """
        Prueba la conexión al proxy para verificar que funciona
        """
        proxy_url = self.get_proxy_stream_url(stream_id)
        if not proxy_url:
            return False

        print(f"🧪 Probando conexión al proxy: {proxy_url}")

        try:
            # Hacer una petición HEAD para verificar
            response = self.session.head(proxy_url)
            if response.status_code == 200:
                print("✅ Proxy accesible y funcionando")
                content_type = response.headers.get('content-type', 'unknown')
                print(f"📋 Content-Type: {content_type}")
                return True
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error conectando al proxy: {e}")
            return False

    def list_available_streams(self, limit: int = 10) -> None:
        """Listar streams disponibles para referencia"""
        try:
            url = f"{self.base_url}/api/channels/streams/?page_size={limit}"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()

            print(f"📋 Streams disponibles (primeros {limit}):")
            for stream in data.get('results', []):
                print(f"  ID: {stream['id']} - Nombre: {stream.get('name', 'Sin nombre')}")

        except Exception as e:
            print(f"❌ Error listando streams: {e}")


def main():
    """Función principal para probar el acceso a streams"""
    if len(sys.argv) < 4:
        print("Uso: python stream_player.py <base_url> <stream_id> <username> <password> [--live|--proxy|--test|--ffmpeg]")
        print("Ejemplos:")
        print("  python stream_player.py http://localhost:5000 123 admin password")
        print("  python stream_player.py http://localhost:5000 123 admin password --live")
        print("  python stream_player.py http://localhost:5000 123 admin password --proxy")
        print("  python stream_player.py http://localhost:5000 123 admin password --test")
        print("  python stream_player.py http://localhost:5000 123 admin password --ffmpeg")
        print("O para listar streams: python stream_player.py <base_url> list <username> <password>")
        sys.exit(1)

    base_url = sys.argv[1]
    action = sys.argv[2]
    username = sys.argv[3]
    password = sys.argv[4]

    # Opciones adicionales
    use_live = '--live' in sys.argv
    use_proxy = '--proxy' in sys.argv
    test_connection = '--test' in sys.argv
    use_ffmpeg = '--ffmpeg' in sys.argv

    # Crear reproductor con credenciales
    player = StreamPlayer(base_url, username, password)

    if action.lower() == 'list':
        # Listar streams disponibles
        player.list_available_streams()
    else:
        # Intentar acceder al stream especificado
        try:
            stream_id = int(action)

            if test_connection:
                # Solo probar conexión
                success = player.test_proxy_connection(stream_id)
            elif use_ffmpeg:
                # Usar con ffmpeg
                success = player.stream_to_ffmpeg(stream_id)
            else:
                # Acceder normalmente
                success = player.play_stream_by_id(
                    stream_id,
                    use_vlc=True,
                    use_live_endpoint=use_live,
                    use_proxy=use_proxy
                )

            sys.exit(0 if success else 1)
        except ValueError:
            print(f"❌ ID de stream inválido: {action}")
            sys.exit(1)


if __name__ == "__main__":
    main()