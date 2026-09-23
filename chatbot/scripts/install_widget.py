#!/usr/bin/env python3
"""Instala el widget del chatbot en todas las páginas HTML locales."""

from __future__ import annotations

import re
from pathlib import Path

SHOP_ROOT = Path(__file__).resolve().parents[2]
WIDGET_PATH = "chatbot/widget/chatbot-widget.js"
WIDGET_TAG = f'<script type="module" src="/{WIDGET_PATH}"></script>'


def install_widget(path: Path) -> bool:
    html = path.read_text(encoding="utf-8", errors="replace")
    if WIDGET_PATH in html:
        return False

    if re.search(r"</body>", html, flags=re.IGNORECASE):
        updated = re.sub(
            r"</body>",
            f"{WIDGET_TAG}\n</body>",
            html,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        updated = f"{html}\n{WIDGET_TAG}\n"

    path.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    changed = 0
    for path in SHOP_ROOT.rglob("*.html"):
        if install_widget(path):
            changed += 1
    print(f"Widget instalado en {changed} páginas nuevas")


if __name__ == "__main__":
    main()
