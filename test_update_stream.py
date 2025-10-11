from api.dispatcharr_client import DispatcharrClient
import os

# Usar las credenciales del archivo .env
client = DispatcharrClient(
    base_url='http://192.168.10.10:9192',
    username='jose',
    password='rotring1010'
)

# Obtener un stream
stream_id = 987
print(f'Obteniendo stream {stream_id}...')

try:
    stream = client.get_stream(stream_id)
    print(f'Stream obtenido: {stream["name"]}')
    print(f'Estadísticas actuales: {stream.get("stream_stats", "None")}')
except Exception as e:
    print(f'Error obteniendo stream: {e}')
    exit(1)

# Intentar actualizar el stream con datos de prueba
print(f'\nIntentando actualizar stream {stream_id}...')
test_data = {
    'name': stream['name'],
    'url': stream['url'],
    'stream_stats': {
        'test_field': 'test_value',
        'output_bitrate': 9999.9
    },
    'stream_stats_updated_at': '2025-10-11T12:00:00.000000Z'
}

try:
    result = client.update_stream(stream_id, test_data)
    print('Actualización exitosa!')
    print(f'Resultado: {result}')
except Exception as e:
    print(f'Error actualizando stream: {e}')

# Verificar si se guardó
print(f'\nVerificando si se guardó...')
try:
    stream_after = client.get_stream(stream_id)
    print(f'Estadísticas después: {stream_after.get("stream_stats", "None")}')
except Exception as e:
    print(f'Error verificando: {e}')