#!/usr/bin/env python3
"""Sincroniza el prompt editable con los workflows importables del chatbot."""

from __future__ import annotations

import json
import re
from pathlib import Path

CHATBOT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = CHATBOT_ROOT / "PROMPT-ASISTENTE.txt"
WORKFLOW_PATHS = [
    CHATBOT_ROOT / "workflows" / "02-chatbot-web.json",
    CHATBOT_ROOT / "workflows" / "04-chatwoot-agent-bot.json",
]


def sync_workflow(path: Path, encoded_prompt: str) -> None:
    workflow = path.read_text(encoding="utf-8")
    pattern = re.compile(r'("systemMessage"\s*:\s*)"(?:\\.|[^"\\])*"')
    updated, replacements = pattern.subn(
        lambda match: f"{match.group(1)}{encoded_prompt}",
        workflow,
        count=1,
    )
    if replacements != 1:
        raise RuntimeError(f"No se encontró un único System Message en {path.name}.")
    path.write_text(updated, encoding="utf-8")
    print(f"Prompt sincronizado: {path}")


def main() -> None:
    prompt = PROMPT_PATH.read_text(encoding="utf-8").strip()
    encoded_prompt = json.dumps(prompt, ensure_ascii=False)
    for path in WORKFLOW_PATHS:
        sync_workflow(path, encoded_prompt)


if __name__ == "__main__":
    main()
