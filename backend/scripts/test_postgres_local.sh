#!/bin/bash
# Quick test script for PostgreSQL local testing

set -e

echo "🔍 Testing with PostgreSQL..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Please start it first."
    exit 1
fi

# Set database URL
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/arandu_test}"

# Create database if it doesn't exist
psql $DATABASE_URL -c "SELECT 1;" > /dev/null 2>&1 || \
    psql postgresql://postgres:postgres@localhost:5432/postgres -c "CREATE DATABASE arandu_test;"

echo "✅ Database ready"

# Enable pg_trgm extension
echo "📦 Enabling pg_trgm extension..."
psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

# Run migrations
echo "🔄 Running migrations..."
cd backend
alembic upgrade head

# Verify current migration
echo "📍 Current migration:"
alembic current

# Run tests
echo "🧪 Running tests..."
pytest -q --tb=short tests/

# Test rollback
echo "⏪ Testing rollback..."
alembic downgrade -1
echo "🔄 Upgrading again..."
alembic upgrade head

echo "✅ All tests passed!"

