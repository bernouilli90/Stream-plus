from api.dispatcharr_client import DispatcharrClient
import os

# Usar las credenciales del archivo .env
client = DispatcharrClient(
    base_url='http://192.168.10.10:9192',
    username='jose',
    password='rotring1010'
)

# Obtener un stream sin estadísticas (usemos el ID 987 que vimos antes)
stream_id = 987
print(f'Verificando stream {stream_id} antes del test...')

# Obtener el stream antes del test
try:
    stream_before = client.get_stream(stream_id)
    print(f'Estadísticas antes: {stream_before.get("stream_stats", "None")}')
    print(f'Fecha actualización antes: {stream_before.get("stream_stats_updated_at", "None")}')
except Exception as e:
    print(f'Error obteniendo stream: {e}')
    exit(1)

print(f'\nProbando stream {stream_id}...')

try:
    result = client.test_stream(stream_id, test_duration=5)
    print('Resultado del test:')
    print(f'Success: {result.get("success")}')
    print(f'Message: {result.get("message")}')

    if result.get('statistics'):
        print('Estadísticas calculadas:')
        stats = result['statistics']
        for key, value in stats.items():
            print(f'  {key}: {value}')

        # Verificar campos de bitrate
        bitrate_fields = ['output_bitrate', 'ffmpeg_output_bitrate', 'video_bitrate', 'bitrate']
        print('\nCampos de bitrate encontrados:')
        for field in bitrate_fields:
            if field in stats:
                print(f'  {field}: {stats[field]}')

    if result.get('save_error'):
        print(f'Error al guardar: {result["save_error"]}')

except Exception as e:
    print(f'Error: {e}')
    exit(1)

print(f'\nVerificando stream {stream_id} después del test...')

# Obtener el stream después del test
try:
    stream_after = client.get_stream(stream_id)
    print(f'Estadísticas después: {stream_after.get("stream_stats", "None")}')
    print(f'Fecha actualización después: {stream_after.get("stream_stats_updated_at", "None")}')
    
    # Verificar si se guardó correctamente
    stats_after = stream_after.get("stream_stats", {})
    if stats_after:
        print('\nEstadísticas guardadas correctamente:')
        for key, value in stats_after.items():
            print(f'  {key}: {value}')
        
        # Verificar específicamente el bitrate
        bitrate_saved = stats_after.get('output_bitrate') or stats_after.get('ffmpeg_output_bitrate')
        if bitrate_saved:
            print(f'\n✓ Bitrate guardado correctamente: {bitrate_saved} kbps')
        else:
            print('\n✗ ERROR: No se guardó el bitrate!')
    else:
        print('\n✗ ERROR: No se guardaron estadísticas!')

except Exception as e:
    print(f'Error obteniendo stream después: {e}')