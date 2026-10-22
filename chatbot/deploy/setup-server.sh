#!/usr/bin/env bash
# Prepara un servidor Ubuntu 24.04 recién creado: Docker, Compose y swap.
# Se ejecuta una sola vez, como usuario con sudo:
#   bash chatbot/deploy/setup-server.sh
set -euo pipefail

if [[ $EUID -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

echo "==> Actualizando paquetes"
$SUDO apt-get update -y
$SUDO apt-get install -y curl git python3 ca-certificates

if ! command -v docker >/dev/null 2>&1; then
  echo "==> Instalando Docker y el plugin Compose"
  curl -fsSL https://get.docker.com | $SUDO sh
else
  echo "==> Docker ya está instalado"
fi

if [[ -n "$SUDO" ]]; then
  $SUDO usermod -aG docker "$USER"
fi

# Chatwoot y Ollama juntos superan los 4 GB en los picos de arranque.
if ! $SUDO swapon --show | grep -q '/swapfile'; then
  echo "==> Creando 2 GB de swap"
  $SUDO fallocate -l 2G /swapfile
  $SUDO chmod 600 /swapfile
  $SUDO mkswap /swapfile
  $SUDO swapon /swapfile
  echo '/swapfile none swap sw 0 0' | $SUDO tee -a /etc/fstab >/dev/null
else
  echo "==> El swap ya existe"
fi

echo
docker --version
docker compose version
echo
echo "Listo. Cierra la sesión SSH y vuelve a entrar para usar docker sin sudo."
echo "Después continúa con: bash chatbot/deploy/configure.sh <dominio> <correo>"
