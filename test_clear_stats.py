#!/usr/bin/env python3
"""
Test script to verify clear_stream_stats functionality
"""
import sys
import os
sys.path.append('.')

from api.dispatcharr_client import DispatcharrClient

def test_clear_stream_stats():
    """Test the clear_stream_stats function"""

    # Configurar cliente
    client = DispatcharrClient(
        base_url=os.getenv('DISPATCHARR_URL', 'http://localhost:8000'),
        username=os.getenv('DISPATCHARR_USERNAME'),
        password=os.getenv('DISPATCHARR_PASSWORD')
    )

    print('🔍 Buscando streams con estadísticas...')

    try:
        streams = client.get_streams(page_size=50)  # Obtener primeros 50 streams
        streams_with_stats = []

        for stream in streams:
            if stream.get('stream_stats') and len(stream.get('stream_stats', {})) > 0:
                streams_with_stats.append(stream)

        print(f'📊 Encontrados {len(streams_with_stats)} streams con estadísticas')

        if not streams_with_stats:
            print('❌ No se encontraron streams con estadísticas para probar')
            return

        # Usar el primer stream con estadísticas para la prueba
        test_stream = streams_with_stats[0]
        stream_id = test_stream['id']
        stream_name = test_stream.get('name', f'Stream {stream_id}')

        print(f'🧪 Probando clear_stream_stats con: {stream_name} (ID: {stream_id})')
        print(f'   Estadísticas antes: {len(test_stream.get("stream_stats", {}))} campos')
        print(f'   Timestamp antes: {test_stream.get("stream_stats_updated_at", "N/A")}')

        # Intentar limpiar las estadísticas
        print(f'🗑️  Limpiando estadísticas del stream {stream_id}...')
        result = client.clear_stream_stats(stream_id)

        if result:
            print('✅ clear_stream_stats ejecutado exitosamente')
            print(f'   Respuesta: {result}')

            # Verificar que las estadísticas se hayan limpiado
            print(f'🔍 Verificando que las estadísticas se hayan limpiado...')
            updated_stream = client.get_stream(stream_id)

            stats_after = updated_stream.get('stream_stats', {})
            timestamp_after = updated_stream.get('stream_stats_updated_at')

            print(f'   Estadísticas después: {len(stats_after)} campos')
            print(f'   Timestamp después: {timestamp_after}')

            if len(stats_after) == 0:
                print('✅ SUCCESS: Las estadísticas se limpiaron correctamente')
                return True
            else:
                print('❌ FAILURE: Las estadísticas NO se limpiaron')
                print(f'   Stats restantes: {stats_after}')
                return False
        else:
            print('❌ FAILURE: clear_stream_stats falló')
            return False

    except Exception as e:
        print(f'❌ Error durante la prueba: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_clear_stream_stats()
    sys.exit(0 if success else 1)