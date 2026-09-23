#!/usr/bin/env python3
"""Crea el inbox web y el AgentBot local de Chatwoot sin guardar el token admin."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

CHATBOT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = CHATBOT_ROOT / ".env"
CONFIG_PATH = CHATBOT_ROOT / "widget" / "chatwoot-config.json"
CHATWOOT_URL = "http://localhost:3000"
INBOX_NAME = "iShop Web"
BOT_NAME = "Asistente iShop"
BOT_WEBHOOK = "http://n8n:5678/webhook/ishop-chatwoot-bot"
WEBSITE_URL = "http://localhost:8080"


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def upsert_env(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen: set[str] = set()
    written: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in line:
            key = line.split("=", 1)[0].strip()
            if key in updates:
                written.append(f"{key}={updates[key]}")
                seen.add(key)
                continue
        written.append(line)
    for key, value in updates.items():
        if key not in seen:
            written.append(f"{key}={value}")
    path.write_text("\n".join(written) + "\n", encoding="utf-8")


def api(
    method: str,
    path: str,
    token: str,
    body: dict[str, object] | None = None,
) -> dict[str, object] | list[object]:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{CHATWOOT_URL}{path}",
        data=payload,
        method=method,
    )
    request.add_header("api_access_token", token)
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} falló ({error.code}): {detail}") from error
    return json.loads(raw) if raw else {}


def wait_for_chatwoot() -> None:
    last_error = "sin respuesta"
    for _ in range(40):
        try:
            urllib.request.urlopen(f"{CHATWOOT_URL}/auth/sign_in", timeout=5)
            return
        except urllib.error.HTTPError:
            return
        except Exception as error:  # noqa: BLE001
            last_error = str(error)
            time.sleep(3)
    raise RuntimeError(f"Chatwoot no responde en {CHATWOOT_URL}: {last_error}")


def find_named(items: list[dict[str, object]], name: str) -> dict[str, object] | None:
    for item in items:
        if str(item.get("name") or "") == name:
            return item
    return None


def main() -> None:
    env = load_env(ENV_PATH)
    access_token = env.get("CHATWOOT_ACCESS_TOKEN", "").strip()
    if not access_token:
        raise SystemExit(
            "Falta CHATWOOT_ACCESS_TOKEN en chatbot/.env.\n"
            "Abre http://localhost:3000, crea el propietario y copia el "
            "Access Token de Profile Settings."
        )

    wait_for_chatwoot()
    profile = api("GET", "/api/v1/profile", access_token)
    accounts = profile.get("accounts") if isinstance(profile, dict) else None
    if not isinstance(accounts, list) or not accounts:
        raise RuntimeError("El token no devolvió ninguna cuenta de Chatwoot.")
    account = accounts[0]
    if not isinstance(account, dict):
        raise RuntimeError("La cuenta de Chatwoot tiene un formato inesperado.")
    account_id = account.get("id")
    if account_id is None:
        raise RuntimeError("No se pudo leer el id de la cuenta.")

    inboxes_payload = api("GET", f"/api/v1/accounts/{account_id}/inboxes", access_token)
    inbox_items = (
        inboxes_payload.get("payload", inboxes_payload)
        if isinstance(inboxes_payload, dict)
        else inboxes_payload
    )
    if not isinstance(inbox_items, list):
        inbox_items = []
    inbox = find_named([item for item in inbox_items if isinstance(item, dict)], INBOX_NAME)
    inbox_body = {
        "name": INBOX_NAME,
        "channel": {
            "type": "web_widget",
            "website_url": WEBSITE_URL,
            "welcome_title": "¿Cómo podemos ayudarte?",
            "welcome_tagline": "Compras, productos y soporte iShop",
            "widget_color": "#EC7B32",
        },
    }
    if inbox is None:
        created = api(
            "POST",
            f"/api/v1/accounts/{account_id}/inboxes",
            access_token,
            inbox_body,
        )
        inbox = created.get("payload", created) if isinstance(created, dict) else created
    if not isinstance(inbox, dict):
        raise RuntimeError("No se pudo crear o leer el inbox web.")
    inbox_id = inbox.get("id")
    website_token = inbox.get("website_token")
    if not website_token:
        fresh = api(
            "GET",
            f"/api/v1/accounts/{account_id}/inboxes/{inbox_id}",
            access_token,
        )
        inbox = fresh.get("payload", fresh) if isinstance(fresh, dict) else fresh
        if not isinstance(inbox, dict):
            raise RuntimeError("El inbox no devolvió website_token.")
        website_token = inbox.get("website_token")
    if not website_token:
        raise RuntimeError("Chatwoot no entregó el token público del widget.")

    bots_payload = api("GET", f"/api/v1/accounts/{account_id}/agent_bots", access_token)
    bot_items = (
        bots_payload.get("payload", bots_payload)
        if isinstance(bots_payload, dict)
        else bots_payload
    )
    if not isinstance(bot_items, list):
        bot_items = []
    bot = find_named([item for item in bot_items if isinstance(item, dict)], BOT_NAME)
    bot_token = env.get("CHATWOOT_BOT_TOKEN", "").strip()
    bot_body = {
        "name": BOT_NAME,
        "description": "AgentBot RAG de iShop. Responde solo en conversaciones pending.",
        "outgoing_url": BOT_WEBHOOK,
        "bot_type": 0,
    }
    if bot is None or not bot_token:
        if isinstance(bot, dict) and bot.get("id") is not None:
            api(
                "DELETE",
                f"/api/v1/accounts/{account_id}/agent_bots/{bot['id']}",
                access_token,
            )
        created_bot = api(
            "POST",
            f"/api/v1/accounts/{account_id}/agent_bots",
            access_token,
            bot_body,
        )
        bot = (
            created_bot.get("payload", created_bot)
            if isinstance(created_bot, dict)
            else created_bot
        )
        if not isinstance(bot, dict):
            raise RuntimeError("No se pudo crear el AgentBot.")
        bot_token = str(bot.get("access_token") or "")
    else:
        api(
            "PATCH",
            f"/api/v1/accounts/{account_id}/agent_bots/{bot['id']}",
            access_token,
            bot_body,
        )
    if not bot_token:
        raise RuntimeError("El AgentBot no devolvió access_token.")

    api(
        "POST",
        f"/api/v1/accounts/{account_id}/inboxes/{inbox_id}/set_agent_bot",
        access_token,
        {"agent_bot": bot.get("id")},
    )

    CONFIG_PATH.write_text(
        json.dumps(
            {
                "baseUrl": CHATWOOT_URL,
                "websiteToken": website_token,
                "inboxName": INBOX_NAME,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    upsert_env(
        ENV_PATH,
        {
            "CHATWOOT_ACCOUNT_ID": str(account_id),
            "CHATWOOT_BOT_TOKEN": bot_token,
        },
    )

    print(f"Cuenta: {account_id}")
    print(f"Inbox: {inbox_id} ({INBOX_NAME})")
    print(f"AgentBot: {bot.get('id')} → {BOT_WEBHOOK}")
    print(f"Widget público: {CONFIG_PATH}")
    print("El token administrativo no se guardó en el repositorio.")
    print("Reinicia n8n para cargar CHATWOOT_BOT_TOKEN:")
    print("  docker compose -f chatbot/compose.yml restart n8n")


if __name__ == "__main__":
    main()
