#!/bin/bash
# deploy.sh - Script di deployment per Reminor su VPS

set -e

echo "=========================================="
echo "   Reminor Deployment Script"
echo "=========================================="

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verifica che .env.production esista
if [ ! -f ".env.production" ]; then
    echo -e "${RED}Errore: .env.production non trovato!${NC}"
    echo "Copia .env.production.template in .env.production e configura le variabili."
    exit 1
fi

# Carica variabili d'ambiente
export $(grep -v '^#' .env.production | xargs)

# Verifica JWT_SECRET_KEY
if [ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" == "CHANGE-THIS-TO-A-SECURE-RANDOM-STRING" ]; then
    echo -e "${RED}Errore: JWT_SECRET_KEY non configurato!${NC}"
    echo "Genera una chiave sicura con: openssl rand -hex 32"
    exit 1
fi

echo -e "${GREEN}[1/4] Pulling latest changes...${NC}"
git pull origin main || true

echo -e "${GREEN}[2/4] Building containers...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

echo -e "${GREEN}[3/4] Stopping old containers...${NC}"
docker-compose -f docker-compose.prod.yml down || true

echo -e "${GREEN}[4/4] Starting services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo -e "${GREEN}=========================================="
echo "   Deployment completato!"
echo "==========================================${NC}"
echo ""
echo "Servizi attivi:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo -e "${YELLOW}Controlla i log con:${NC}"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo -e "${YELLOW}L'app sarà disponibile su:${NC}"
echo "  https://app.reminor.it"
echo ""
