#!/bin/sh
set -e

# Banner de inicio
echo "=========================================="
echo "  Stream Plus Docker Container"
echo "=========================================="
echo ""

# Verificar variables de entorno requeridas
if [ -z "$DISPATCHARR_API_URL" ]; then
    echo "ERROR: DISPATCHARR_API_URL no está configurada"
    echo "Ejemplo: -e DISPATCHARR_API_URL=http://dispatcharr:8080"
    exit 1
fi

if [ -z "$DISPATCHARR_API_USER" ]; then
    echo "ERROR: DISPATCHARR_API_USER no está configurada"
    echo "Ejemplo: -e DISPATCHARR_API_USER=admin"
    exit 1
fi

if [ -z "$DISPATCHARR_API_PASSWORD" ]; then
    echo "ERROR: DISPATCHARR_API_PASSWORD no está configurada"
    echo "Ejemplo: -e DISPATCHARR_API_PASSWORD=password"
    exit 1
fi

# Mostrar configuración (sin mostrar la contraseña)
echo "Configuración:"
echo "  - API URL: $DISPATCHARR_API_URL"
echo "  - API User: $DISPATCHARR_API_USER"
echo "  - Puerto: ${PORT:-5000}"
echo "  - Debug: ${FLASK_DEBUG:-False}"
echo "  - Usuario: $(id -u):$(id -g)"
echo ""

# Verificar que el directorio de reglas existe
if [ ! -d "/app/rules" ]; then
    echo "ADVERTENCIA: Directorio /app/rules no encontrado"
    echo "Se creará automáticamente, pero considera mapear un volumen para persistencia"
    mkdir -p /app/rules
fi

# Crear archivos de reglas por defecto si no existen
if [ ! -f "/app/rules/auto_assignment_rules.json" ]; then
    echo "Creando auto_assignment_rules.json por defecto..."
    echo '{"rules": []}' > /app/rules/auto_assignment_rules.json
fi

if [ ! -f "/app/rules/sorting_rules.json" ]; then
    echo "Creando sorting_rules.json por defecto..."
    echo '{"rules": []}' > /app/rules/sorting_rules.json
fi

# Crear enlaces simbólicos si las reglas están en /app/rules
if [ -f "/app/rules/auto_assignment_rules.json" ] && [ ! -f "/app/auto_assignment_rules.json" ]; then
    ln -sf /app/rules/auto_assignment_rules.json /app/auto_assignment_rules.json
fi

if [ -f "/app/rules/sorting_rules.json" ] && [ ! -f "/app/sorting_rules.json" ]; then
    ln -sf /app/rules/sorting_rules.json /app/sorting_rules.json
fi

echo "=========================================="
echo "  Iniciando Stream Plus..."
echo "=========================================="
echo ""

# Ejecutar el comando proporcionado
exec "$@"
