#!/usr/bin/env python3
"""Prueba el AgentBot de iShop a través de la API local de Chatwoot."""

from __future__ import annotations

import json
import os
import time
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CHATBOT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = CHATBOT_ROOT / ".env"
CHATWOOT_URL = os.environ.get("CHATWOOT_URL", "http://localhost:3000").rstrip("/")
RESPONSE_TIMEOUT_SECONDS = 45


@dataclass(frozen=True)
class TestCase:
    question: str
    expected_any: tuple[str, ...]
    forbidden: tuple[str, ...] = ()


TEST_CASES = (
    TestCase("hola", ("hola",)),
    TestCase(
        "busco una laptop para programar, tengo 2000",
        ("macbook air",),
        ("adaptador", "multipuerto"),
    ),
    TestCase(
        "compara la opcion 1 y la 2",
        ("comparacion", "opcion 1"),
        ("thule",),
    ),
    TestCase(
        "ahora quiero un microfno",
        ("no encontre", "no vende"),
        ("soundlink micro",),
    ),
    TestCase("mejor un relok", ("apple watch",)),
    TestCase("cuanto cuesta el envio a domicilio", ("$6", "6")),
    TestCase("que tarjetas aceptan para pagar", ("visa", "mastercard", "tarjeta")),
    TestCase("cuanto dura la garantia", ("1 ano", "garantia")),
    TestCase("tienen servicio tecnico autorizado", ("servicio tecnico", "autorizado")),
    TestCase("quiero ver iphone 17", ("iphone 17",)),
    TestCase("quiero audifonos para el gimnasio", ("audif", "auricular", "jbl")),
    TestCase("busco una mochila para mi macbook", ("mochila",)),
)


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.lower())
    return "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    )


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def wait_for_chatwoot() -> None:
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(
                f"{CHATWOOT_URL}/auth/sign_in",
                timeout=5,
            )
            return
        except urllib.error.HTTPError:
            return
        except (ConnectionError, OSError, urllib.error.URLError):
            time.sleep(2)
    raise RuntimeError("Chatwoot no respondió después de 120 segundos")


def request_json(
    method: str,
    url: str,
    token: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={
            "api_access_token": token,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = response.read().decode()
    return json.loads(raw) if raw else {}


def messages(api: str, conversation_id: int, token: str) -> list[dict[str, Any]]:
    response = request_json(
        "GET",
        f"{api}/conversations/{conversation_id}/messages",
        token,
    )
    payload = response.get("payload", [])
    return payload if isinstance(payload, list) else []


def send_and_wait(
    api: str,
    conversation_id: int,
    token: str,
    question: str,
) -> tuple[float, str]:
    previous = {
        message["id"]
        for message in messages(api, conversation_id, token)
        if message.get("message_type") == 1 and not message.get("private")
    }
    started = time.perf_counter()
    request_json(
        "POST",
        f"{api}/conversations/{conversation_id}/messages",
        token,
        {"content": question, "message_type": 0, "private": False},
    )
    deadline = time.monotonic() + RESPONSE_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        time.sleep(0.25)
        outgoing = [
            message
            for message in messages(api, conversation_id, token)
            if message.get("message_type") == 1
            and not message.get("private")
            and message.get("id") not in previous
        ]
        if outgoing:
            elapsed = time.perf_counter() - started
            return elapsed, str(outgoing[-1].get("content", ""))
    return time.perf_counter() - started, ""


def main() -> None:
    env = load_env()
    token = env.get("CHATWOOT_ACCESS_TOKEN", "")
    account_id = env.get("CHATWOOT_ACCOUNT_ID", "")
    if not token or not account_id:
        raise SystemExit(
            "Faltan CHATWOOT_ACCESS_TOKEN o CHATWOOT_ACCOUNT_ID en chatbot/.env"
        )

    wait_for_chatwoot()
    api = f"{CHATWOOT_URL}/api/v1/accounts/{account_id}"
    inboxes_response = request_json("GET", f"{api}/inboxes", token)
    inboxes = inboxes_response.get("payload", [])
    inbox = next(
        (
            item
            for item in inboxes
            if isinstance(item, dict) and item.get("name") == "iShop Web"
        ),
        None,
    )
    inbox_id = inbox.get("id") if inbox else None
    if not inbox_id:
        raise RuntimeError(
            "No existe el inbox 'iShop Web'. Ejecuta setup_chatwoot.py primero."
        )

    unique = int(time.time())
    contact_response = request_json(
        "POST",
        f"{api}/contacts",
        token,
        {
            "inbox_id": inbox_id,
            "name": "Prueba automática RAG",
            "email": f"qa-rag-{unique}@ishop.local",
        },
    )
    contact = contact_response.get("payload", {}).get("contact", {})
    contact_id = contact.get("id")
    if not contact_id:
        raise RuntimeError("Chatwoot no devolvió el contacto de prueba")

    conversation = request_json(
        "POST",
        f"{api}/conversations",
        token,
        {"inbox_id": inbox_id, "contact_id": contact_id, "status": "pending"},
    )
    conversation_id = conversation.get("id")
    if not conversation_id:
        raise RuntimeError("Chatwoot no devolvió la conversación de prueba")

    failures: list[str] = []
    timings: list[float] = []
    print(f"Conversación de prueba: {conversation_id}")
    for index, case in enumerate(TEST_CASES, start=1):
        elapsed, answer = send_and_wait(
            api,
            int(conversation_id),
            token,
            case.question,
        )
        timings.append(elapsed)
        normalized_answer = normalize(answer)
        expected = any(
            normalize(fragment) in normalized_answer
            for fragment in case.expected_any
        )
        forbidden = [
            fragment
            for fragment in case.forbidden
            if normalize(fragment) in normalized_answer
        ]
        passed = bool(answer) and expected and not forbidden
        status = "OK" if passed else "FALLO"
        print(f"{index:02d}. {status} {elapsed:5.2f}s — {case.question}")
        if not passed:
            failures.append(
                f"{case.question}: respuesta={answer!r}, prohibidos={forbidden}"
            )

    elapsed, handoff_answer = send_and_wait(
        api,
        int(conversation_id),
        token,
        "quiero hablar con un asesor humano",
    )
    timings.append(elapsed)
    time.sleep(2)
    final_conversation = request_json(
        "GET",
        f"{api}/conversations/{conversation_id}",
        token,
    )
    handoff_ok = (
        final_conversation.get("status") == "open"
        and "asesor" in normalize(handoff_answer)
    )
    print(
        f"13. {'OK' if handoff_ok else 'FALLO'} {elapsed:5.2f}s "
        "— handoff a asesor"
    )
    if not handoff_ok:
        failures.append(
            "Handoff: "
            f"estado={final_conversation.get('status')}, "
            f"respuesta={handoff_answer!r}"
        )

    average = sum(timings) / len(timings)
    print()
    print(f"Resultado: {len(timings) - len(failures)}/{len(timings)} correctas")
    print(f"Tiempo promedio: {average:.2f}s")
    if failures:
        print("\nFallos:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
