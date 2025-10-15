# Reproductor de Streams Alternativo

Este script implementa una forma alternativa de acceder a streams específicos por ID sin modificar el código existente del cliente Dispatcharr.

## Características

- ✅ **Acceso directo a streams por ID**
- ✅ **Autenticación integrada en URL** (compatible con VLC)
- ✅ **Proxy autenticado** (compatible con ffmpeg)
- ✅ **Búsqueda automática de canales**
- ✅ **Múltiples opciones**: VLC, URLs, proxy, ffmpeg
- ✅ **Sin modificaciones**: No altera el código existente del proyecto

## Uso Básico

### Desde línea de comandos

```bash
# Acceder con URLs con credenciales (compatible con VLC)
python stream_player.py http://localhost:5000 123 admin password

# Usar endpoint /live/ alternativo
python stream_player.py http://localhost:5000 123 admin password --live

# Usar proxy autenticado (compatible con ffmpeg)
python stream_player.py http://localhost:5000 123 admin password --proxy

# Probar conexión al proxy
python stream_player.py http://localhost:5000 123 admin password --test

# Procesar con ffmpeg
python stream_player.py http://localhost:5000 123 admin password --ffmpeg

# Listar streams disponibles
python stream_player.py http://localhost:5000 list admin password
```

### Desde código Python

```python
from stream_player import StreamPlayer

# Crear reproductor con credenciales (OBLIGATORIO)
player = StreamPlayer(
    base_url="http://localhost:5000",
    username="admin",
    password="tu_password"
)

# Obtener URL del proxy para usar con ffmpeg
proxy_url = player.get_proxy_stream_url(123)
print(f"Usa esta URL con ffmpeg: {proxy_url}")

# Procesar directamente con ffmpeg
success = player.stream_to_ffmpeg(123)

# Probar conexión al proxy
success = player.test_proxy_connection(123)

# Acceder con URLs con credenciales (VLC)
success = player.play_stream_by_id(123, use_vlc=True)
```

## Modos de Acceso

### 1. **URLs con Credenciales** (Para VLC/Reproductores)
- **Estándar**: `/{username}/{password}/{channel_id}`
- **Live**: `/live/{username}/{password}/{channel_id}`
- ✅ Compatible con VLC, MPV, etc.
- ❌ Requiere credenciales en URL

### 2. **Proxy Autenticado** (Para ffmpeg/Processamiento)
- **Endpoint**: `/proxy/ts/stream/{channel_id}`
- ✅ Compatible con ffmpeg, curl, etc.
- ✅ Autenticación automática via Bearer token
- ❌ No compatible con reproductores externos

## Requisitos

- Python 3.6+
- VLC Media Player (opcional, para reproducción)
- ffmpeg (opcional, para procesamiento)
- **Credenciales de usuario** (obligatorio para streaming)
- Acceso a la API de Dispatcharr

## Métodos disponibles

- `get_proxy_stream_url(stream_id)`: Obtiene URL del proxy autenticado
- `stream_to_ffmpeg(stream_id, command)`: Procesa stream con ffmpeg
- `test_proxy_connection(stream_id)`: Prueba conexión al proxy
- `play_stream_by_id(stream_id, use_vlc, use_live, use_proxy)`: Acceso general
- `get_stream_info(stream_id)`: Obtiene información del stream
- `find_channel_by_stream(stream_id)`: Encuentra canal que contiene el stream

## Ejemplos de uso con ffmpeg

```bash
# Ver información del stream
ffmpeg -i "$(python stream_player.py http://localhost:5000 123 admin password --proxy)" -f null -

# Convertir a archivo
ffmpeg -i "$(python stream_player.py http://localhost:5000 123 admin password --proxy)" -c copy output.mp4

# Transmitir a otro destino
ffmpeg -i "$(python stream_player.py http://localhost:5000 123 admin password --proxy)" -f flv rtmp://destino/stream
```

## Solución al problema original

Si tenías problemas con ffmpeg accediendo directamente a URLs de streams, ahora puedes:

1. **Usar el proxy autenticado**: `--proxy` para URLs que ffmpeg puede usar
2. **Autenticación automática**: No necesitas manejar tokens manualmente
3. **Compatibilidad total**: Funciona con cualquier herramienta que soporte HTTP

## Ejemplos

Ejecuta `python ejemplo_stream_player.py` para ver ejemplos completos de uso.

1. **Autenticación**: Se conecta a la API usando JWT si se proporcionan credenciales
2. **Búsqueda**: Busca automáticamente el canal que contiene el stream especificado
3. **Proxy**: Usa el sistema de proxy de Dispatcharr (`/proxy/ts/stream/{channel_id}`)
4. **Reproducción**: Abre VLC con la URL del stream o muestra la URL para uso manual

## Requisitos

- Python 3.6+
- VLC Media Player (opcional, para reproducción automática)
- Acceso a la API de Dispatcharr

## Métodos disponibles

- `play_stream_by_id(stream_id, use_vlc=True)`: Reproduce un stream específico
- `get_stream_info(stream_id)`: Obtiene información detallada de un stream
- `find_channel_by_stream(stream_id)`: Encuentra el canal que contiene un stream
- `list_available_streams(limit=10)`: Lista streams disponibles

## Ejemplos

Ejecuta `python ejemplo_stream_player.py` para ver ejemplos completos de uso.

## Notas

- Si no se encuentra VLC, el script mostrará la URL para reproducción manual
- Funciona tanto con streams autenticados como públicos
- Es completamente independiente del código existente del cliente</content>
<parameter name="filePath">c:\Users\josea\Desktop\Stream-plus\Stream-plus\STREAM_PLAYER_README.md