from api.dispatcharr_client import DispatcharrClient
from models import RulesManager, AutoAssignmentRule
import json

# Crear cliente de Dispatcharr
dispatcharr_client = DispatcharrClient(
    base_url='http://192.168.10.10:9192',
    username='jose',
    password='rotring1010'
)

# Crear manager de reglas
rules_manager = RulesManager()

# Crear una regla de prueba
rule = AutoAssignmentRule(
    id=0,  # Se asignará automáticamente
    name='Test Rule - Statistics Saving',
    channel_id=614,  # Canal existente
    enabled=True,
    replace_existing_streams=False,
    regex_pattern='Точка отрыва',  # Patrón que coincida con stream 985
    test_streams_before_sorting=True,  # ¡Esto es clave!
    force_retest_old_streams=True,  # Forzar retest
    retest_days_threshold=0  # Retest inmediato
)

print(f'Creando regla: {rule.name}')

# Guardar la regla
created_rule = rules_manager.create_rule(rule)
print(f'Regla creada con ID: {created_rule.id}')

# Obtener todas las reglas para verificar
all_rules = rules_manager.load_rules()
print(f'Total de reglas: {len(all_rules)}')

# Encontrar nuestra regla
test_rule = None
for r in all_rules:
    if r.name == 'Test Rule - Statistics Saving':
        test_rule = r
        break

if test_rule:
    print(f'Regla encontrada: {test_rule.name} (ID: {test_rule.id})')
    print(f'Configuración: test_streams_before_sorting={test_rule.test_streams_before_sorting}')

    # Ahora vamos a ejecutar la regla para probar que guarda estadísticas
    print('\nEjecutando regla para probar guardado de estadísticas...')

    # Obtener streams
    streams = dispatcharr_client.get_streams()
    print(f'Total streams: {len(streams)}')

    # Filtrar streams que coincidan con el patrón
    import re
    matching_streams = []
    for stream in streams:
        if stream.get('name') and re.search(rule.regex_pattern, stream.get('name', '')):
            matching_streams.append(stream)

    print(f'Streams que coinciden con patrón "{rule.regex_pattern}": {len(matching_streams)}')
    for stream in matching_streams[:3]:  # Mostrar primeros 3
        print(f'  - Stream {stream["id"]}: {stream.get("name", "Sin nombre")}')

    if matching_streams:
        # Probar test_stream en uno de los streams
        test_stream = matching_streams[0]
        stream_id = test_stream['id']
        stream_name = test_stream.get('name', f'Stream {stream_id}')

        print(f'\nProbando stream {stream_id}: {stream_name}')

        # Verificar si ya tiene estadísticas
        has_stats_before = test_stream.get('stream_stats') is not None
        print(f'Tiene estadísticas antes: {has_stats_before}')

        # Ejecutar test_stream
        result = dispatcharr_client.test_stream(stream_id)
        print(f'Resultado del test: success={result.get("success")}, save_error={result.get("save_error")}')

        if result.get('success') and not result.get('save_error'):
            print('✓ Test exitoso - estadísticas deberían haberse guardado')

            # Verificar que se guardaron las estadísticas
            updated_stream = dispatcharr_client.get_stream(stream_id)
            has_stats_after = updated_stream.get('stream_stats') is not None

            print(f'Tiene estadísticas después: {has_stats_after}')

            if has_stats_after:
                stats = updated_stream['stream_stats']
                print('Estadísticas guardadas:')
                for key, value in stats.items():
                    print(f'  {key}: {value}')
            else:
                print('❌ ERROR: Las estadísticas no se guardaron')
        else:
            print(f'❌ Test falló: {result.get("save_error", result.get("message", "Error desconocido"))}')
    else:
        print('No se encontraron streams que coincidan con el patrón')

else:
    print('❌ No se pudo encontrar la regla creada')