#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

if ! grep -q '^CHATWOOT_SECRET_KEY_BASE=.\+' .env; then
  secret="$(python3 -c 'import secrets; print(secrets.token_hex(64))')"
  if grep -q '^CHATWOOT_SECRET_KEY_BASE=' .env; then
    python3 - "$secret" <<'PY'
from pathlib import Path
import sys
path = Path(".env")
secret = sys.argv[1]
text = path.read_text(encoding="utf-8")
lines = []
for line in text.splitlines():
    if line.startswith("CHATWOOT_SECRET_KEY_BASE="):
        lines.append(f"CHATWOOT_SECRET_KEY_BASE={secret}")
    else:
        lines.append(line)
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
  else
    printf '\nCHATWOOT_SECRET_KEY_BASE=%s\n' "$secret" >> .env
  fi
fi

docker compose up -d chatwoot-postgres chatwoot-redis qdrant ollama

echo "Esperando PostgreSQL de Chatwoot..."
for _ in $(seq 1 40); do
  if docker compose exec -T chatwoot-postgres pg_isready -U postgres >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if [[ ! -f .chatwoot-prepared ]]; then
  echo "Preparando la base de Chatwoot la primera vez..."
  docker compose run --rm --no-deps chatwoot bundle exec rails db:chatwoot_prepare
  touch .chatwoot-prepared
fi

docker compose up -d

echo
echo "Servicios iniciados:"
echo "- n8n:      http://localhost:5678"
echo "- Qdrant:   http://localhost:6333/dashboard"
echo "- Ollama:   http://localhost:11434"
echo "- Chatwoot: http://localhost:3000"
echo "- Tienda:   http://localhost:8080"
echo
echo "La primera vez:"
echo "1. Crea el usuario propietario en n8n y en Chatwoot."
echo "2. Copia el token de Profile Settings de Chatwoot a CHATWOOT_ACCESS_TOKEN en chatbot/.env"
echo "3. Ejecuta: python3 chatbot/scripts/setup_chatwoot.py"
echo "4. Reinicia n8n: docker compose -f chatbot/compose.yml restart n8n"
