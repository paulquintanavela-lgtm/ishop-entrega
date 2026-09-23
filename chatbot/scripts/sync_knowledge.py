#!/usr/bin/env python3
"""Genera documentos Markdown para la base RAG usando la copia local de iShop."""

from __future__ import annotations

import json
import re
import urllib.request
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

CHATBOT_ROOT = Path(__file__).resolve().parents[1]
SHOP_ROOT = CHATBOT_ROOT.parent
KNOWLEDGE_DIR = CHATBOT_ROOT / "knowledge"
PRODUCTS_URL = "https://ec.tiendasishop.com/products.json?limit=250"
PRODUCT_IMAGES_PATH = KNOWLEDGE_DIR / "product-images.json"
PUBLIC_PAGES = {
    "Preguntas frecuentes": "pages/preguntas-frecuentes/index.html",
    "Devolución y garantía": "pages/politicas-de-devolucion-cambio-garantia/index.html",
    "Servicio técnico": "pages/servicio-tecnico-apple-en-ecuador/index.html",
    "Ventas corporativas": "pages/ventas-corporativas/index.html",
    "Tiendas físicas": "pages/tiendas-fisicas/index.html",
    "Contacto": "pages/contacto/index.html",
    "Términos y condiciones": "pages/terminos-y-condiciones/index.html",
}


class MainContentParser(HTMLParser):
    """Extrae texto visible únicamente del elemento main-content."""

    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attrs_map = dict(attrs)
        if tag == "main" and attrs_map.get("id") == "main-content":
            self.depth = 1
            return
        if not self.depth:
            return
        self.depth += 1
        if tag in {"script", "style", "svg", "noscript"}:
            self.skip_depth += 1
        if not self.skip_depth and tag in {"h1", "h2", "h3", "p", "li", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if not self.depth:
            return
        if tag in {"script", "style", "svg", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
        self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.depth and not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        raw = unescape(" ".join(self.parts))
        lines = [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()]
        return "\n".join(line for line in lines if line)


def fetch_products() -> list[dict[str, Any]]:
    request = urllib.request.Request(
        PRODUCTS_URL,
        headers={"User-Agent": "iShop-RAG-Demo/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    products = payload.get("products", [])
    if not isinstance(products, list):
        raise ValueError("La respuesta del catálogo no contiene una lista de productos")
    return [
        product
        for product in products
        if any(variant.get("available") for variant in product.get("variants", []))
    ]


def product_markdown(product: dict[str, Any]) -> str:
    title = str(product.get("title", "Producto sin nombre")).strip()
    handle = str(product.get("handle", "")).strip()
    product_url = f"https://ec.tiendasishop.com/products/{handle}" if handle else ""
    product_type = str(product.get("product_type", "")).strip()
    vendor = str(product.get("vendor", "")).strip()
    body_html = str(product.get("body_html", ""))
    description = re.sub(r"<[^>]+>", " ", body_html)
    description = re.sub(r"\s+", " ", unescape(description)).strip()
    if len(description) > 1200:
        description = f"{description[:1200].rstrip()}…"
    tags = product.get("tags", [])
    tag_text = ", ".join(str(tag) for tag in tags) if isinstance(tags, list) else str(tags)

    variants: list[str] = []
    for variant in product.get("variants", []):
        if not variant.get("available"):
            continue
        variant_title = str(variant.get("title", "")).strip()
        price = str(variant.get("price", "")).strip()
        variants.append(f"- {variant_title}: ${price} (disponible públicamente)")

    lines = [
        f"## {title}",
        f"- URL: {product_url}",
        f"- Tipo: {product_type or 'No especificado'}",
        f"- Marca: {vendor or 'No especificada'}",
        f"- Etiquetas: {tag_text or 'Sin etiquetas'}",
        f"- Descripción: {description or 'Sin descripción pública'}",
        "- Variantes:",
        *(variants or ["- Sin variantes públicas"]),
        "",
    ]
    return "\n".join(lines)


def write_catalog(products: list[dict[str, Any]]) -> Path:
    destination = KNOWLEDGE_DIR / "catalogo-productos.md"
    content = [
        "# Catálogo público de iShop Ecuador",
        "",
        f"Fuente: {PRODUCTS_URL}",
        f"Productos incluidos: {len(products)}",
        "",
        "Los precios y la disponibilidad corresponden a la consulta pública realizada al generar este archivo.",
        "El asistente debe indicar que pueden cambiar y enlazar la ficha del producto.",
        "",
    ]
    content.extend(product_markdown(product) for product in products)
    destination.write_text("\n".join(content), encoding="utf-8")
    return destination


def write_product_images(products: list[dict[str, Any]]) -> Path:
    image_by_handle: dict[str, str] = {}
    for product in products:
        handle = str(product.get("handle", "")).strip()
        images = product.get("images", [])
        if not handle or not isinstance(images, list) or not images:
            continue
        first_image = images[0]
        if not isinstance(first_image, dict):
            continue
        source = str(first_image.get("src", "")).strip()
        if source:
            image_by_handle[handle] = source

    PRODUCT_IMAGES_PATH.write_text(
        json.dumps(image_by_handle, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PRODUCT_IMAGES_PATH


def extract_page(path: Path) -> str:
    parser = MainContentParser()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    return parser.text()


def write_public_content() -> Path:
    destination = KNOWLEDGE_DIR / "contenido-publico-ishop.md"
    sections = [
        "# Información pública de iShop Ecuador",
        "",
        "Fuente: páginas de la copia local del sitio.",
        "",
    ]
    for title, relative_path in PUBLIC_PAGES.items():
        path = SHOP_ROOT / relative_path
        if not path.exists():
            continue
        text = extract_page(path)
        if not text:
            continue
        sections.extend(
            [
                f"## {title}",
                f"Ruta: /{relative_path.removesuffix('/index.html')}",
                "",
                text,
                "",
            ]
        )
    destination.write_text("\n".join(sections), encoding="utf-8")
    return destination


def main() -> None:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    products = fetch_products()
    catalog_path = write_catalog(products)
    images_path = write_product_images(products)
    content_path = write_public_content()
    print(f"Catálogo generado: {catalog_path} ({len(products)} productos)")
    print(f"Imágenes generadas: {images_path}")
    print(f"Contenido generado: {content_path}")


if __name__ == "__main__":
    main()
