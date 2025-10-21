#!/usr/bin/env python3
"""
Test script to verify clear_stream_stats functionality without requiring live Dispatcharr
"""
import sys
import os
sys.path.append('.')

from api.dispatcharr_client import DispatcharrClient
from unittest.mock import Mock, patch

def test_clear_stream_stats_logic():
    """Test the clear_stream_stats function logic without network calls"""

    print('🧪 Probando la lógica de clear_stream_stats...')

    # Crear cliente mock
    client = DispatcharrClient('http://dummy')

    # Verificar que la función existe
    assert hasattr(client, 'clear_stream_stats'), "❌ Función clear_stream_stats no existe"
    assert callable(client.clear_stream_stats), "❌ clear_stream_stats no es callable"

    print('✅ Función clear_stream_stats existe y es callable')

    # Verificar la signatura de la función
    import inspect
    sig = inspect.signature(client.clear_stream_stats)
    expected_params = ['stream_id']
    actual_params = list(sig.parameters.keys())

    assert actual_params == expected_params, f"❌ Parámetros incorrectos. Esperado: {expected_params}, Actual: {actual_params}"

    print('✅ Signatura de función correcta')

    # Mock del método patch_stream para verificar qué datos se envían
    with patch.object(client, 'patch_stream') as mock_patch:
        mock_patch.return_value = {'id': 123, 'name': 'Test Stream'}

        # Llamar a clear_stream_stats
        result = client.clear_stream_stats(123)

        # Verificar que patch_stream fue llamado con los datos correctos
        mock_patch.assert_called_once_with(123, {'stream_stats': {}})

        # Verificar el resultado
        assert result == {'id': 123, 'name': 'Test Stream'}, f"❌ Resultado incorrecto: {result}"

    print('✅ Lógica de clear_stream_stats funciona correctamente')
    print('   - Envía PATCH con stream_stats: {}')
    print('   - Retorna el resultado de patch_stream')

    return True

def test_clear_stream_stats_error_handling():
    """Test error handling in clear_stream_stats"""

    print('🧪 Probando manejo de errores en clear_stream_stats...')

    client = DispatcharrClient('http://dummy')

    # Mock patch_stream para que lance una excepción
    with patch.object(client, 'patch_stream') as mock_patch:
        mock_patch.side_effect = Exception("API Error")

        try:
            client.clear_stream_stats(123)
            assert False, "❌ Debería haber lanzado una excepción"
        except Exception as e:
            assert str(e) == "API Error", f"❌ Excepción incorrecta: {e}"

    print('✅ Manejo de errores funciona correctamente')
    print('   - Propaga excepciones de patch_stream')

    return True

def test_patch_stream_method():
    """Test the patch_stream method that clear_stream_stats uses"""

    print('🧪 Probando método patch_stream subyacente...')

    client = DispatcharrClient('http://dummy')

    # Verificar que patch_stream existe
    assert hasattr(client, 'patch_stream'), "❌ Método patch_stream no existe"
    assert callable(client.patch_stream), "❌ patch_stream no es callable"

    # Verificar signatura
    import inspect
    sig = inspect.signature(client.patch_stream)
    expected_params = ['stream_id', 'stream_data']
    actual_params = list(sig.parameters.keys())

    assert actual_params == expected_params, f"❌ Parámetros incorrectos. Esperado: {expected_params}, Actual: {actual_params}"

    print('✅ Método patch_stream existe y tiene signatura correcta')

    return True

if __name__ == '__main__':
    try:
        print('🚀 Iniciando pruebas de clear_stream_stats...\n')

        success1 = test_clear_stream_stats_logic()
        print()

        success2 = test_clear_stream_stats_error_handling()
        print()

        success3 = test_patch_stream_method()
        print()

        if success1 and success2 and success3:
            print('🎉 Todas las pruebas pasaron exitosamente!')
            print('✅ La función clear_stream_stats está implementada correctamente')
            sys.exit(0)
        else:
            print('❌ Algunas pruebas fallaron')
            sys.exit(1)

    except Exception as e:
        print(f'❌ Error durante las pruebas: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)