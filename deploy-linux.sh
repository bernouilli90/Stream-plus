#!/bin/bash
# Stream Plus - Linux Deployment Script
# This script automates the initial setup on a Linux server

set -e

echo "========================================"
echo "  Stream Plus - Linux Deployment"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Pre-flight checks
echo -e "${BLUE}Step 1: Running pre-flight checks...${NC}"
if [ -f "./docker-precheck.sh" ]; then
    chmod +x docker-precheck.sh
    ./docker-precheck.sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}Pre-flight checks failed. Please fix errors before continuing.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Warning: docker-precheck.sh not found, skipping...${NC}"
fi

echo ""

# Step 2: Set execute permissions
echo -e "${BLUE}Step 2: Setting execute permissions...${NC}"
chmod +x docker-build.sh docker-helper.sh docker-entrypoint.sh 2>/dev/null || true
echo -e "${GREEN}✓ Execute permissions set${NC}"

echo ""

# Step 3: Configuration
echo -e "${BLUE}Step 3: Configuration${NC}"
echo -e "${YELLOW}Please edit docker-compose.yml and set these variables:${NC}"
echo "  - DISPATCHARR_API_URL"
echo "  - DISPATCHARR_API_USER"
echo "  - DISPATCHARR_API_PASSWORD"
echo ""
read -p "Have you configured docker-compose.yml? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Please configure docker-compose.yml and run this script again.${NC}"
    echo "Example:"
    echo "  nano docker-compose.yml"
    exit 0
fi

echo ""

# Step 4: Build image
echo -e "${BLUE}Step 4: Building Docker image...${NC}"
./docker-build.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}Build failed.${NC}"
    exit 1
fi

echo ""

# Step 5: Create rules directory
echo -e "${BLUE}Step 5: Creating rules directory...${NC}"
mkdir -p ./rules
echo -e "${GREEN}✓ Rules directory created${NC}"

echo ""

# Step 6: Start container
echo -e "${BLUE}Step 6: Starting container...${NC}"
docker-compose up -d
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to start container.${NC}"
    exit 1
fi

echo ""

# Step 7: Wait for container to be healthy
echo -e "${BLUE}Step 7: Waiting for container to be healthy...${NC}"
echo -n "Waiting"
for i in {1..30}; do
    if docker inspect stream-plus | grep -q '"Status": "healthy"'; then
        echo ""
        echo -e "${GREEN}✓ Container is healthy${NC}"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

echo ""

# Step 8: Verification
echo -e "${BLUE}Step 8: Verification${NC}"
echo ""

echo -e "${GREEN}Container status:${NC}"
docker ps | grep stream-plus

echo ""
echo -e "${GREEN}Container logs:${NC}"
docker logs --tail 20 stream-plus

echo ""
echo "========================================"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo "========================================"
echo ""
echo "Access Stream Plus at: http://localhost:5000"
echo ""
echo "Useful commands:"
echo "  View logs:        ./docker-helper.sh logs"
echo "  Execute rules:    ./docker-helper.sh exec-all"
echo "  View rule files:  ./docker-helper.sh rules"
echo "  Stop container:   ./docker-helper.sh stop"
echo "  Restart:          ./docker-helper.sh restart"
echo ""
echo "Set up cron for automation:"
echo "  crontab -e"
echo "  0 * * * * docker exec stream-plus python execute_rules.py --all"
echo ""
echo "See DOCKER_QUICKSTART.md for more information"
echo ""
