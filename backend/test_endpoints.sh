#!/bin/bash
# Script para testar endpoints da API

echo "=== Testando Health Check ==="
curl -s http://localhost:8000/health | jq . || curl -s http://localhost:8000/health

echo -e "\n\n=== Criando um job fake ==="
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/testuser/testrepo"}')

echo "$JOB_RESPONSE" | jq . || echo "$JOB_RESPONSE"

JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.job_id // empty')

if [ -n "$JOB_ID" ]; then
  echo -e "\n\n=== Obtendo detalhes do job ==="
  curl -s http://localhost:8000/api/v1/jobs/$JOB_ID | jq . || curl -s http://localhost:8000/api/v1/jobs/$JOB_ID
  
  echo -e "\n\n=== Obtendo status do job ==="
  curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/status | jq . || curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/status
fi
