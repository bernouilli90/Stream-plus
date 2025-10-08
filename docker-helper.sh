#!/bin/bash
# Stream Plus Docker - Helper Script
# Simplifica la ejecución de comandos comunes en el contenedor

set -e

CONTAINER_NAME="stream-plus"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para verificar si el contenedor está corriendo
check_container() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${RED}Error: El contenedor '${CONTAINER_NAME}' no está corriendo${NC}"
        echo -e "${YELLOW}Inicia el contenedor con: docker-compose up -d${NC}"
        exit 1
    fi
}

# Función de ayuda
show_help() {
    echo -e "${BLUE}Stream Plus Docker Helper${NC}"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo ""
    echo -e "${GREEN}Gestión del contenedor:${NC}"
    echo "  start           - Iniciar el contenedor"
    echo "  stop            - Detener el contenedor"
    echo "  restart         - Reiniciar el contenedor"
    echo "  logs            - Ver logs en tiempo real"
    echo "  status          - Ver estado del contenedor"
    echo "  shell           - Abrir shell en el contenedor"
    echo ""
    echo -e "${GREEN}Ejecución de reglas:${NC}"
    echo "  exec-assign     - Ejecutar reglas de asignación"
    echo "  exec-sort       - Ejecutar reglas de ordenación"
    echo "  exec-all        - Ejecutar todas las reglas"
    echo "  exec-rule ID    - Ejecutar regla específica por ID"
    echo ""
    echo -e "${GREEN}Información:${NC}"
    echo "  rules           - Listar reglas configuradas"
    echo "  env             - Ver variables de entorno"
    echo "  health          - Ver estado de salud del contenedor"
    echo ""
    echo -e "${GREEN}Otros:${NC}"
    echo "  build           - Reconstruir la imagen"
    echo "  update          - Actualizar y reiniciar"
    echo "  help            - Mostrar esta ayuda"
    echo ""
}

# Comandos
case "${1}" in
    start)
        echo -e "${BLUE}Iniciando Stream Plus...${NC}"
        docker-compose up -d
        echo -e "${GREEN}✓ Contenedor iniciado${NC}"
        ;;
    
    stop)
        echo -e "${BLUE}Deteniendo Stream Plus...${NC}"
        docker-compose down
        echo -e "${GREEN}✓ Contenedor detenido${NC}"
        ;;
    
    restart)
        echo -e "${BLUE}Reiniciando Stream Plus...${NC}"
        docker-compose restart
        echo -e "${GREEN}✓ Contenedor reiniciado${NC}"
        ;;
    
    logs)
        echo -e "${BLUE}Mostrando logs (Ctrl+C para salir)...${NC}"
        docker-compose logs -f
        ;;
    
    status)
        echo -e "${BLUE}Estado del contenedor:${NC}"
        docker-compose ps
        ;;
    
    shell)
        check_container
        echo -e "${BLUE}Abriendo shell en el contenedor...${NC}"
        docker exec -it ${CONTAINER_NAME} sh
        ;;
    
    exec-assign)
        check_container
        echo -e "${BLUE}Ejecutando reglas de asignación...${NC}"
        docker exec ${CONTAINER_NAME} python execute_rules.py --assignment --verbose
        ;;
    
    exec-sort)
        check_container
        echo -e "${BLUE}Ejecutando reglas de ordenación...${NC}"
        docker exec ${CONTAINER_NAME} python execute_rules.py --sorting --verbose
        ;;
    
    exec-all)
        check_container
        echo -e "${BLUE}Ejecutando todas las reglas...${NC}"
        docker exec ${CONTAINER_NAME} python execute_rules.py --all --verbose
        ;;
    
    exec-rule)
        check_container
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Debes especificar el ID de la regla${NC}"
            echo "Uso: $0 exec-rule ID"
            exit 1
        fi
        echo -e "${BLUE}Ejecutando regla ID $2...${NC}"
        docker exec ${CONTAINER_NAME} python execute_rules.py --all --rule-ids $2 --verbose
        ;;
    
    rules)
        check_container
        echo -e "${BLUE}Reglas de asignación:${NC}"
        docker exec ${CONTAINER_NAME} cat /app/rules/auto_assignment_rules.json 2>/dev/null || \
        docker exec ${CONTAINER_NAME} cat /app/auto_assignment_rules.json
        echo ""
        echo -e "${BLUE}Reglas de ordenación:${NC}"
        docker exec ${CONTAINER_NAME} cat /app/rules/sorting_rules.json 2>/dev/null || \
        docker exec ${CONTAINER_NAME} cat /app/sorting_rules.json
        ;;
    
    env)
        check_container
        echo -e "${BLUE}Variables de entorno:${NC}"
        docker exec ${CONTAINER_NAME} env | grep -E "(DISPATCHARR|FLASK|PORT|SECRET)" | sort
        ;;
    
    health)
        echo -e "${BLUE}Estado de salud:${NC}"
        docker inspect ${CONTAINER_NAME} --format='{{json .State.Health}}' | jq '.'
        ;;
    
    build)
        echo -e "${BLUE}Reconstruyendo imagen...${NC}"
        docker-compose build --no-cache
        echo -e "${GREEN}✓ Imagen reconstruida${NC}"
        ;;
    
    update)
        echo -e "${BLUE}Actualizando Stream Plus...${NC}"
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        echo -e "${GREEN}✓ Stream Plus actualizado y reiniciado${NC}"
        ;;
    
    help|--help|-h|"")
        show_help
        ;;
    
    *)
        echo -e "${RED}Error: Comando desconocido '${1}'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
