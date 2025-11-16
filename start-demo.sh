#!/bin/bash
# Script to start local Arandu demo

set -e

echo "🚀 Iniciando demo local do Arandu CoReview Studio..."
echo ""

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker primeiro."
    exit 1
fi

# Navegar para infra
cd "$(dirname "$0")/infra"

echo "📦 Iniciando serviços com Docker Compose..."
echo ""

# Iniciar serviços
docker compose up --build

