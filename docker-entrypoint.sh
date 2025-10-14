#!/bin/sh
set -e

# Banner de inicio
echo "=========================================="
echo "  Stream Plus Docker Container"
echo "=========================================="
echo ""

# Función para cambiar UID/GID si es necesario (estilo LinuxServer)
change_uid_gid() {
    # Valores por defecto durante el build
    DEFAULT_UID=1000
    DEFAULT_GID=1000

    # Valores actuales del usuario
    CURRENT_UID=$(id -u streamplus)
    CURRENT_GID=$(id -g streamplus)

    # Verificar si necesitamos cambiar UID/GID
    if [ "$USER_UID" != "$DEFAULT_UID" ] || [ "$USER_GID" != "$DEFAULT_GID" ]; then
        echo "Cambiando UID:GID de $CURRENT_UID:$CURRENT_GID a $USER_UID:$USER_GID..."

        # Cambiar GID si es necesario
        if [ "$USER_GID" != "$CURRENT_GID" ]; then
            # Verificar si el grupo ya existe con otro GID
            if getent group $USER_GID >/dev/null 2>&1; then
                # El grupo existe, cambiar el nombre del grupo existente
                EXISTING_GROUP=$(getent group $USER_GID | cut -d: -f1)
                groupmod -n streamplus_temp "$EXISTING_GROUP" 2>/dev/null || true
            fi

            # Cambiar GID del grupo streamplus
            groupmod -g $USER_GID streamplus
        fi

        # Cambiar UID si es necesario
        if [ "$USER_UID" != "$CURRENT_UID" ]; then
            # Verificar si el usuario ya existe con otro UID
            if getent passwd $USER_UID >/dev/null 2>&1; then
                # El usuario existe, cambiar el nombre del usuario existente
                EXISTING_USER=$(getent passwd $USER_UID | cut -d: -f1)
                usermod -l streamplus_temp "$EXISTING_USER" 2>/dev/null || true
            fi

            # Cambiar UID del usuario streamplus
            usermod -u $USER_UID streamplus
        fi

        # Cambiar ownership de todos los archivos en /app
        echo "Actualizando ownership de archivos..."
        chown -R streamplus:streamplus /app

        echo "UID:GID actualizado exitosamente a $USER_UID:$USER_GID"
    fi
}

# Cambiar UID/GID si es necesario
change_uid_gid

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
