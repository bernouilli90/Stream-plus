#!/usr/bin/env python3
"""
Test different approaches to clear stream_stats in Dispatcharr
"""
import sys
import os
sys.path.append('.')

from api.dispatcharr_client import DispatcharrClient
from unittest.mock import Mock, patch

def test_clear_stream_stats_approaches():
    """Test different approaches to clear stream_stats"""

    print('🧪 Probando diferentes enfoques para limpiar stream_stats...\n')

    client = DispatcharrClient('http://dummy')

    test_cases = [
        {
            'name': 'Current approach: empty dict only',
            'data': {'stream_stats': {}}
        },
        {
            'name': 'Empty dict + None timestamp',
            'data': {'stream_stats': {}, 'stream_stats_updated_at': None}
        },
        {
            'name': 'Empty dict + null timestamp',
            'data': {'stream_stats': {}, 'stream_stats_updated_at': 'null'}
        },
        {
            'name': 'Only timestamp removal',
            'data': {'stream_stats_updated_at': None}
        },
        {
            'name': 'Only timestamp to null',
            'data': {'stream_stats_updated_at': 'null'}
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f'{i}. {test_case["name"]}')
        print(f'   Data: {test_case["data"]}')

        # Mock patch_stream
        with patch.object(client, 'patch_stream') as mock_patch:
            mock_patch.return_value = {'id': 123, 'stream_stats': {}, 'stream_stats_updated_at': None}

            try:
                result = client.clear_stream_stats(123)
                print('   ✅ Método ejecutado sin error')
                print(f'   📤 Envió: {test_case["data"]}')

                # Verificar qué se llamó
                call_args = mock_patch.call_args
                if call_args:
                    called_data = call_args[0][1]  # Segundo argumento de patch_stream
                    print(f'   📥 Recibió: {called_data}')

                    if called_data == test_case["data"]:
                        print('   ✅ Datos enviados correctamente')
                    else:
                        print('   ⚠️  Datos enviados diferentes a los esperados')
                else:
                    print('   ❌ patch_stream no fue llamado')

            except Exception as e:
                print(f'   ❌ Error: {e}')

        print()

    print('💡 Posibles soluciones:')
    print('1. Usar solo {"stream_stats": {}} (enfoque actual)')
    print('2. Verificar si la API acepta {"stream_stats": {}, "stream_stats_updated_at": null}')
    print('3. Usar PUT en lugar de PATCH para reemplazar completamente el objeto')
    print('4. Verificar la documentación de la API de Dispatcharr')

def test_put_vs_patch():
    """Test using PUT instead of PATCH to clear stats"""

    print('🧪 Probando PUT vs PATCH para limpiar estadísticas...\n')

    client = DispatcharrClient('http://dummy')

    # Mock _make_request to capture what method is used
    with patch.object(client, '_make_request') as mock_request:
        mock_request.return_value = {'id': 123, 'stream_stats': {}}

        # Test current PATCH approach
        print('1. Enfoque actual (PATCH):')
        try:
            result = client.clear_stream_stats(123)
            call_args = mock_request.call_args
            if call_args:
                method, endpoint, data = call_args[0][:3]
                print(f'   Método: {method}')
                print(f'   Endpoint: {endpoint}')
                print(f'   Data: {data}')
        except Exception as e:
            print(f'   ❌ Error: {e}')

    print()
    print('2. Enfoque alternativo (PUT completo):')
    print('   Idea: Obtener stream completo, limpiar stats, enviar PUT con objeto completo')
    print('   Ventaja: Más control sobre el estado final')
    print('   Desventaja: Más complejo, requiere GET adicional')

if __name__ == '__main__':
    test_clear_stream_stats_approaches()
    print()
    test_put_vs_patch()