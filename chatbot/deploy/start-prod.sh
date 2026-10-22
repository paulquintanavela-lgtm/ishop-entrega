#!/usr/bin/env bash
# Levanta el stack en el servidor. Revisa que el .env de producción esté
# completo y reutiliza start.sh, que toma el override desde COMPOSE_FILE.
#
#   bash chatbot/deploy/start-prod.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "Falta chatbot/.env. Ejecuta primero deploy/configure.sh" >&2
  exit 1
fi

value() {
  grep -m1 "^$1=" .env | cut -d= -f2- || true
}

missing=()
for key in SITE_DOMAIN CHAT_DOMAIN N8N_DOMAIN ACME_EMAIL \
  CHATWOOT_SECRET_KEY_BASE CHATWOOT_POSTGRES_PASSWORD GEMINI_API_KEY; do
  if [[ -z "$(value "$key")" ]]; then
    missing+=("$key")
  fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "Faltan valores en chatbot/.env: ${missing[*]}" >&2
  exit 1
fi

if ! grep -q '^COMPOSE_FILE=.*compose\.prod\.yml' .env; then
  echo "chatbot/.env no apunta a compose.prod.yml. Ejecuta deploy/configure.sh" >&2
  exit 1
fi

bash start.sh

site="$(value SITE_DOMAIN)"
echo
echo "Servicios públicos:"
echo "- Tienda:   https://$site"
echo "- Chatwoot: https://$(value CHAT_DOMAIN)"
echo "- n8n:      https://$(value N8N_DOMAIN)"
echo
echo "El primer certificado HTTPS puede tardar un minuto. Si falla, revisa:"
echo "  docker compose logs -f caddy"
