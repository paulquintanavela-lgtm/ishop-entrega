#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
docker compose down

echo "Servicios detenidos. Los volúmenes de n8n, Qdrant, Ollama y Chatwoot se conservan."
