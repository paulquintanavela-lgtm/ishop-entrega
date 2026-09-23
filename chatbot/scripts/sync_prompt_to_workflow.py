#!/usr/bin/env python3
"""Sincroniza el prompt editable con el workflow importable del chatbot."""

from __future__ import annotations

import json
import re
from pathlib import Path

CHATBOT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = CHATBOT_ROOT / "PROMPT-ASISTENTE.txt"
WORKFLOW_PATH = CHATBOT_ROOT / "workflows" / "02-chatbot-web.json"


def main() -> None:
    prompt = PROMPT_PATH.read_text(encoding="utf-8").strip()
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    encoded_prompt = json.dumps(prompt, ensure_ascii=False)
    pattern = re.compile(r'("systemMessage"\s*:\s*)"(?:\\.|[^"\\])*"')
    updated, replacements = pattern.subn(
        lambda match: f"{match.group(1)}{encoded_prompt}",
        workflow,
        count=1,
    )
    if replacements != 1:
        raise RuntimeError("No se encontró un único System Message en el workflow.")
    WORKFLOW_PATH.write_text(updated, encoding="utf-8")
    print(f"Prompt sincronizado: {WORKFLOW_PATH}")


if __name__ == "__main__":
    main()
