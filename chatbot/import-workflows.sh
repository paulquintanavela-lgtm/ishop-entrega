#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
docker compose exec -T n8n n8n import:workflow \
  --separate \
  --input=/files/workflows

echo "Workflows importados. Recarga http://localhost:5678"
