from models import RulesManager
from api.dispatcharr_client import DispatcharrClient
import re

# Cargar reglas
rules_manager = RulesManager()
rules = rules_manager.load_rules()

# Usar la regla ID 3 (Dazn La)
rule = None
for r in rules:
    if r.id == 3:
        rule = r
        break

if not rule:
    print('Regla ID 3 no encontrada')
    exit(1)

print(f'Usando regla: {rule.name}')
print(f'test_streams_before_sorting: {rule.test_streams_before_sorting}')

# Crear cliente
client = DispatcharrClient(
    base_url='http://192.168.10.10:9192',
    username='jose',
    password='rotring1010'
)

# Obtener streams
streams = client.get_streams()
print(f'Total streams: {len(streams)}')

# Encontrar streams que coincidan con el patrón de la regla
matching_streams = []
for stream in streams:
    name = stream.get('name', '')
    if rule.regex_pattern and re.search(rule.regex_pattern, name, re.IGNORECASE):
        matching_streams.append(stream)

print(f'Streams que coinciden: {len(matching_streams)}')

# Tomar el primer stream que no tenga estadísticas
test_stream = None
for stream in matching_streams:
    if not stream.get('stream_stats'):
        test_stream = stream
        break

if not test_stream:
    print('No se encontraron streams sin estadísticas que coincidan')
    exit(1)

stream_id = test_stream['id']
stream_name = test_stream.get('name', f'Stream {stream_id}')

print(f'Probando stream {stream_id}: {stream_name}')
print(f'Tenía estadísticas antes: {test_stream.get("stream_stats") is not None}')

# Ejecutar test_stream
result = client.test_stream(stream_id)
print(f'Resultado: success={result.get("success")}, save_error={result.get("save_error")}')

# Verificar si se guardaron las estadísticas
updated_stream = client.get_stream(stream_id)
has_stats_after = updated_stream.get('stream_stats') is not None

print(f'Tiene estadísticas después: {has_stats_after}')

if has_stats_after:
    stats = updated_stream['stream_stats']
    print('Estadísticas guardadas:')
    print(f'  Bitrate: {stats.get("output_bitrate", "N/A")} kbps')
    print(f'  Resolución: {stats.get("resolution", "N/A")}')
    print(f'  Video codec: {stats.get("video_codec", "N/A")}')
else:
    print('ERROR: Las estadísticas no se guardaron')