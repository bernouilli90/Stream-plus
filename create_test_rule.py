import requests
import json

# Crear una regla de prueba para verificar que las estadísticas se guarden
rule_data = {
    'name': 'Test Rule - Statistics Saving',
    'channel_id': 614,  # Usar el canal que ya existe
    'enabled': True,
    'replace_existing_streams': False,
    'regex_pattern': 'Точка отрыва',  # Para que coincida con el stream 985 que no tiene estadísticas
    'test_streams_before_sorting': True,  # Esto es clave - probar streams antes de ordenar
    'force_retest_old_streams': True,  # Forzar retest de streams antiguos
    'retest_days_threshold': 0  # Retest inmediatamente
}

# Hacer la petición POST a la aplicación local
response = requests.post(
    'http://localhost:5000/api/auto-assign-rules',
    json=rule_data,
    headers={'Content-Type': 'application/json'}
)

print(f'Status: {response.status_code}')
if response.status_code == 200:
    result = response.json()
    print(f'Regla creada exitosamente: {result["name"]} (ID: {result["id"]})')
else:
    print(f'Error: {response.text}')