#!/bin/bash
# Script para construir la imagen Docker de Stream Plus

set -e

echo "=========================================="
echo "  Stream Plus - Docker Build"
echo "=========================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Obtener UID y GID del usuario actual (Linux/Mac)
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    USER_UID=$(id -u)
    USER_GID=$(id -g)
    echo -e "${BLUE}Detectado sistema Unix-like${NC}"
    echo -e "  UID: ${GREEN}${USER_UID}${NC}"
    echo -e "  GID: ${GREEN}${USER_GID}${NC}"
else
    # Valores por defecto para Windows
    USER_UID=1000
    USER_GID=1000
    echo -e "${YELLOW}Sistema no Unix, usando valores por defecto${NC}"
    echo -e "  UID: ${GREEN}${USER_UID}${NC}"
    echo -e "  GID: ${GREEN}${USER_GID}${NC}"
fi

echo ""

# Nombre y tag de la imagen
IMAGE_NAME="stream-plus"
IMAGE_TAG="${1:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${BLUE}Construyendo imagen: ${GREEN}${FULL_IMAGE_NAME}${NC}"
echo ""

# Construir la imagen
docker build \
    --build-arg USER_UID=${USER_UID} \
    --build-arg USER_GID=${USER_GID} \
    -t ${FULL_IMAGE_NAME} \
    -f Dockerfile \
    .

echo ""
echo -e "${GREEN}✓ Imagen construida exitosamente${NC}"
echo ""

# Mostrar información de la imagen
echo "Información de la imagen:"
docker images ${IMAGE_NAME} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""
echo -e "${BLUE}Comandos útiles:${NC}"
echo -e "  Iniciar con docker-compose: ${GREEN}docker-compose up -d${NC}"
echo -e "  Iniciar con docker run:     ${GREEN}docker run -d -p 5000:5000 --name stream-plus --env-file .env -v ./rules:/app/rules ${FULL_IMAGE_NAME}${NC}"
echo -e "  Ver logs:                   ${GREEN}docker logs -f stream-plus${NC}"
echo -e "  Ejecutar CLI:               ${GREEN}docker exec stream-plus python execute_rules.py --all${NC}"
echo ""
