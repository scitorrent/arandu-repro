#!/bin/bash
# Script to start local Arandu demo

set -e

echo "🚀 Starting local Arandu CoReview Studio demo..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Navigate to infra
cd "$(dirname "$0")/infra"

echo "📦 Starting services with Docker Compose..."
echo ""

# Start services
docker compose up --build

