#!/usr/bin/env bash
# Escribe chatbot/.env para producción a partir del dominio base.
# Conserva los tokens y secretos que ya existan.
#
#   bash chatbot/deploy/configure.sh ishop-pierre.duckdns.org correo@ejemplo.com
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Uso: bash chatbot/deploy/configure.sh <dominio-base> <correo>" >&2
  echo "Ejemplo: bash chatbot/deploy/configure.sh ishop-pierre.duckdns.org paul@ejemplo.com" >&2
  exit 1
fi

SITE_DOMAIN="${1#http://}"
SITE_DOMAIN="${SITE_DOMAIN#https://}"
SITE_DOMAIN="${SITE_DOMAIN%/}"
ACME_EMAIL="$2"

cd "$(dirname "$0")/.."
ENV_FILE=".env"

current() {
  if [[ -f "$ENV_FILE" ]]; then
    grep -m1 "^$1=" "$ENV_FILE" | cut -d= -f2- || true
  fi
}

SECRET_KEY_BASE="$(current CHATWOOT_SECRET_KEY_BASE)"
POSTGRES_PASSWORD="$(current CHATWOOT_POSTGRES_PASSWORD)"
ACCESS_TOKEN="$(current CHATWOOT_ACCESS_TOKEN)"
BOT_TOKEN="$(current CHATWOOT_BOT_TOKEN)"
HUMAN_AGENT="$(current CHATWOOT_HUMAN_AGENT_EMAIL)"
GEMINI_API_KEY="$(current GEMINI_API_KEY)"
SIGNUP="$(current ENABLE_ACCOUNT_SIGNUP)"

[[ -n "$SECRET_KEY_BASE" ]] || SECRET_KEY_BASE="$(openssl rand -hex 64)"
if [[ -z "$POSTGRES_PASSWORD" || "$POSTGRES_PASSWORD" == "ishop_chatwoot_local" ]]; then
  POSTGRES_PASSWORD="$(openssl rand -hex 24)"
fi
[[ -n "$SIGNUP" ]] || SIGNUP="true"

if [[ -f "$ENV_FILE" ]]; then
  cp "$ENV_FILE" "$ENV_FILE.bak"
  echo "Copia de seguridad: chatbot/$ENV_FILE.bak"
fi

cat > "$ENV_FILE" <<ENV
# Producción de iShop. Generado por deploy/configure.sh. No se sube a Git.

# Hace que "docker compose" en esta carpeta use siempre el override de producción.
COMPOSE_FILE=compose.yml:compose.prod.yml
GENERIC_TIMEZONE=America/Guayaquil

# Dominios que atiende Caddy. El certificado HTTPS se pide para los tres.
SITE_DOMAIN=$SITE_DOMAIN
CHAT_DOMAIN=chat.$SITE_DOMAIN
N8N_DOMAIN=n8n.$SITE_DOMAIN
ACME_EMAIL=$ACME_EMAIL

# URLs públicas que usan los scripts y el widget del navegador.
WEBSITE_URL=https://$SITE_DOMAIN
CHATWOOT_PUBLIC_URL=https://chat.$SITE_DOMAIN
N8N_PUBLIC_URL=https://n8n.$SITE_DOMAIN

# Chatwoot.
CHATWOOT_SECRET_KEY_BASE=$SECRET_KEY_BASE
CHATWOOT_POSTGRES_PASSWORD=$POSTGRES_PASSWORD
CHATWOOT_ACCOUNT_ID=1
CHATWOOT_ACCESS_TOKEN=$ACCESS_TOKEN
CHATWOOT_BOT_TOKEN=$BOT_TOKEN
# Correo del asesor que recibe los traspasos. Vacío = primer administrador.
CHATWOOT_HUMAN_AGENT_EMAIL=$HUMAN_AGENT
# Déjalo en true hasta crear el usuario propietario y luego cámbialo a false.
ENABLE_ACCOUNT_SIGNUP=$SIGNUP

# API key gratuita de Google AI Studio.
GEMINI_API_KEY=$GEMINI_API_KEY
ENV

chmod 600 "$ENV_FILE"

echo "chatbot/.env listo para:"
echo "- Tienda:   https://$SITE_DOMAIN"
echo "- Chatwoot: https://chat.$SITE_DOMAIN"
echo "- n8n:      https://n8n.$SITE_DOMAIN"
if [[ -z "$GEMINI_API_KEY" ]]; then
  echo
  echo "Falta GEMINI_API_KEY en chatbot/.env antes de levantar el stack."
fi
