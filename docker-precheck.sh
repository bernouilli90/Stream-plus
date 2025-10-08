#!/bin/bash
# Script de verificación pre-build para Docker
# Verifica que todo esté listo antes de construir la imagen

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo -e "  Stream Plus - Pre-Build Check"
echo -e "==========================================${NC}"
echo ""

# Contador de errores y advertencias
ERRORS=0
WARNINGS=0

# Función para verificar
check_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

check_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

check_error() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

# 1. Verificar Docker instalado
echo -e "${BLUE}Verificando Docker...${NC}"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    check_ok "Docker instalado: $DOCKER_VERSION"
else
    check_error "Docker no está instalado"
fi

# 2. Verificar Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    check_ok "Docker Compose instalado: $COMPOSE_VERSION"
else
    check_error "Docker Compose no está instalado"
fi

# 3. Verificar que Docker está corriendo
if docker info &> /dev/null; then
    check_ok "Docker daemon está corriendo"
else
    check_error "Docker daemon no está corriendo"
fi

echo ""

# 4. Verificar archivos necesarios
echo -e "${BLUE}Verificando archivos necesarios...${NC}"

FILES=(
    "Dockerfile"
    "docker-compose.yml"
    "docker-entrypoint.sh"
    "requirements.txt"
    "app.py"
    "start.py"
    "models.py"
    "stream_sorter_models.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        check_ok "Archivo encontrado: $file"
    else
        check_error "Archivo faltante: $file"
    fi
done

echo ""

# 5. Verificar directorios
echo -e "${BLUE}Verificando directorios...${NC}"

DIRS=(
    "api"
    "static"
    "templates"
    "rules"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        check_ok "Directorio encontrado: $dir"
    else
        check_error "Directorio faltante: $dir"
    fi
done

echo ""

# 6. Verificar configuración en docker-compose.yml
echo -e "${BLUE}Verificando configuración...${NC}"

if grep -q "DISPATCHARR_API_URL=http://dispatcharr:8080" docker-compose.yml; then
    check_warning "DISPATCHARR_API_URL usa valor por defecto (dispatcharr:8080)"
    echo "          → Asegúrate de cambiar esto a tu servidor Dispatcharr real"
fi

if grep -q "DISPATCHARR_API_USER=admin" docker-compose.yml; then
    check_warning "DISPATCHARR_API_USER usa valor por defecto (admin)"
    echo "          → Cambia esto a tu usuario real"
fi

if grep -q "DISPATCHARR_API_PASSWORD=changeme" docker-compose.yml; then
    check_warning "DISPATCHARR_API_PASSWORD usa valor por defecto"
    echo "          → ¡IMPORTANTE! Cambia la contraseña antes de usar en producción"
fi

if grep -q "SECRET_KEY=change-this-secret-key-in-production" docker-compose.yml; then
    check_warning "SECRET_KEY usa valor por defecto"
    echo "          → Cambia esto en producción"
fi

echo ""

# 7. Verificar permisos
echo -e "${BLUE}Verificando permisos...${NC}"

if [ -x "docker-build.sh" ]; then
    check_ok "docker-build.sh tiene permisos de ejecución"
else
    check_warning "docker-build.sh no es ejecutable"
    echo "          → Ejecuta: chmod +x docker-build.sh"
fi

if [ -x "docker-helper.sh" ]; then
    check_ok "docker-helper.sh tiene permisos de ejecución"
else
    check_warning "docker-helper.sh no es ejecutable"
    echo "          → Ejecuta: chmod +x docker-helper.sh"
fi

if [ -x "docker-entrypoint.sh" ]; then
    check_ok "docker-entrypoint.sh tiene permisos de ejecución"
else
    check_warning "docker-entrypoint.sh no es ejecutable (se arreglará en el build)"
fi

echo ""

# 8. Verificar .dockerignore
echo -e "${BLUE}Verificando .dockerignore...${NC}"

if [ -f ".dockerignore" ]; then
    check_ok ".dockerignore existe"
else
    check_warning ".dockerignore no existe (imagen puede ser más grande)"
fi

echo ""

# 9. Verificar puertos
echo -e "${BLUE}Verificando puertos...${NC}"

if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    check_warning "Puerto 5000 está en uso"
    echo "          → Cambia el puerto en docker-compose.yml o detén el servicio"
else
    check_ok "Puerto 5000 está disponible"
fi

echo ""

# 10. Espacio en disco
echo -e "${BLUE}Verificando espacio en disco...${NC}"

AVAILABLE=$(df -h . | awk 'NR==2 {print $4}')
check_ok "Espacio disponible: $AVAILABLE"

echo ""

# Resumen
echo -e "${BLUE}=========================================="
echo -e "  Resumen"
echo -e "==========================================${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ Todo listo para construir la imagen Docker${NC}"
    echo ""
    echo "Siguiente paso:"
    echo "  ./docker-build.sh"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS advertencia(s) encontrada(s)${NC}"
    echo "  Puedes continuar, pero revisa las advertencias arriba"
    echo ""
    echo "Siguiente paso:"
    echo "  ./docker-build.sh"
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(es) encontrado(s)${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS advertencia(s) encontrada(s)${NC}"
    fi
    echo ""
    echo "Por favor, corrige los errores antes de continuar"
    exit 1
fi
