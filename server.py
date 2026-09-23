#!/usr/bin/env python3
"""Servidor local que sirve la copia de iShop y clona páginas faltantes."""

from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from localize import ORIGIN, ROOT, clone_page, is_content_path, page_file

HOST = "127.0.0.1"
PORT = 8080


class LocalShopHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        clean = path.rstrip("/") or "/"

        if clean != "/" and is_content_path(clean):
            dest = page_file(clean)
            if not dest.exists():
                clone_page(clean)
            if dest.exists():
                self.path = "/" + str(dest.relative_to(ROOT)).replace("\\", "/")

        super().do_GET()

    def log_message(self, format: str, *args) -> None:
        sys_stdout = __import__("sys").stdout
        sys_stdout.write("%s - %s\n" % (self.address_string(), format % args))
        sys_stdout.flush()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    server = ThreadingHTTPServer((HOST, args.port), LocalShopHandler)
    print(f"iShop local en http://{HOST}:{args.port}/")
    print(f"Origen de clonado: {ORIGIN}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido")


if __name__ == "__main__":
    main()
