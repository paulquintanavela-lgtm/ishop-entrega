#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
docker compose up -d

echo
echo "Servicios iniciados:"
echo "- n8n:    http://localhost:5678"
echo "- Qdrant: http://localhost:6333/dashboard"
echo "- Tienda: http://localhost:8080"
echo
echo "La primera vez, crea el usuario propietario en n8n y configura las credenciales."
