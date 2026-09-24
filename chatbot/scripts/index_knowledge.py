#!/usr/bin/env python3
"""Indexa productos y contenido público como documentos RAG independientes."""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

CHATBOT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = CHATBOT_ROOT / "knowledge"
CATALOG_PATH = KNOWLEDGE_DIR / "catalogo-productos.md"
PUBLIC_CONTENT_PATH = KNOWLEDGE_DIR / "contenido-publico-ishop.md"

OLLAMA_URL = "http://localhost:11434"
QDRANT_URL = "http://localhost:6333"
EMBEDDING_MODEL = "nomic-embed-text:latest"
COLLECTION = "ishop_rag_v2"
VECTOR_SIZE = 768
BATCH_SIZE = 24


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode()
    return json.loads(raw) if raw else {}


def normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def extract_field(block: str, name: str) -> str:
    match = re.search(rf"^- {re.escape(name)}: (.+)$", block, re.MULTILINE)
    return match.group(1).strip() if match else ""


def product_category(title: str, product_type: str, tags: str) -> str:
    title_key = normalized(title)
    type_key = normalized(product_type)
    tags_key = normalized(tags)
    accessory_words = (
        "adaptador",
        "cable",
        "cargador",
        "case",
        "funda",
        "hardcase",
        "teclado",
        "mouse",
        "correa",
        "protector",
        "soporte",
        "llavero",
    )
    if title_key.startswith("macbook"):
        return "macbook"
    if title_key.startswith("iphone"):
        return "iphone"
    if title_key.startswith("ipad"):
        return "ipad"
    if title_key.startswith("apple watch"):
        return "watch"
    if title_key.startswith("airpods"):
        return "airpods"
    if title_key.startswith(("imac", "mac mini", "mac studio")):
        return "mac_desktop"
    if any(word in title_key for word in accessory_words) or "accesorios" in tags_key:
        return "accessory"
    if any(word in f"{title_key} {type_key}" for word in ("audifono", "auricular", "parlante", "audio")):
        return "audio"
    return "other"


def parse_products() -> list[dict[str, Any]]:
    raw = CATALOG_PATH.read_text(encoding="utf-8")
    products: list[dict[str, Any]] = []
    for block in raw.split("\n## ")[1:]:
        title, _, remainder = block.partition("\n")
        title = title.strip()
        url = extract_field(remainder, "URL")
        product_type = extract_field(remainder, "Tipo")
        brand = extract_field(remainder, "Marca")
        tags = extract_field(remainder, "Etiquetas")
        description = extract_field(remainder, "Descripción")
        prices = [
            float(value)
            for value in re.findall(r"\$(\d+(?:\.\d+)?)", remainder)
        ]
        variants_section = remainder.partition("- Variantes:")[2]
        variants = [
            line.removeprefix("- ").strip()
            for line in variants_section.splitlines()
            if line.startswith("- ")
        ][:8]
        variants_text = "\n".join(variants)
        if not title or not url or not prices:
            continue
        category = product_category(title, product_type, tags)
        text = "\n".join(
            (
                title,
                f"Categoría: {category}",
                f"Tipo: {product_type}",
                f"Marca: {brand}",
                f"Etiquetas: {tags}",
                f"Precio desde: ${min(prices):.2f}",
            )
        )
        content = "\n".join(
            (
                f"Producto: {title}",
                f"URL: {url}",
                f"Categoría: {category}",
                f"Tipo: {product_type or 'No especificado'}",
                f"Marca: {brand or 'No especificada'}",
                f"Precio desde: ${min(prices):.2f}",
                f"Variantes disponibles:\n{variants_text or 'No detalladas'}",
                f"Descripción: {description[:900] or 'No disponible'}",
            )
        )
        products.append(
            {
                "text": text,
                "content": content,
                "payload": {
                    "doc_kind": "product",
                    "category": category,
                    "title": title,
                    "url": url,
                    "product_type": product_type,
                    "brand": brand,
                    "tags": tags,
                    "min_price": min(prices),
                    "variants": variants_text,
                    "description": description[:900],
                },
            }
        )
    return products


def parse_public_content() -> list[dict[str, Any]]:
    raw = PUBLIC_CONTENT_PATH.read_text(encoding="utf-8")
    documents: list[dict[str, Any]] = []
    for block in raw.split("\n## ")[1:]:
        title, _, content = block.partition("\n")
        title = title.strip()
        content = content.strip()
        if not title or not content:
            continue
        documents.append(
            {
                "text": f"{title}\n{content}",
                "payload": {
                    "doc_kind": "information",
                    "category": normalized(title).replace(" ", "_"),
                    "title": title,
                    "content": content,
                },
            }
        )
    return documents


def embeddings(texts: list[str]) -> list[list[float]]:
    result = request_json(
        "POST",
        f"{OLLAMA_URL}/api/embed",
        {"model": EMBEDDING_MODEL, "input": texts, "keep_alive": -1},
    )
    vectors = result.get("embeddings", [])
    if len(vectors) != len(texts):
        raise RuntimeError("Ollama no devolvió un embedding por documento")
    return vectors


def recreate_collection() -> None:
    try:
        request_json("DELETE", f"{QDRANT_URL}/collections/{COLLECTION}")
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    request_json(
        "PUT",
        f"{QDRANT_URL}/collections/{COLLECTION}",
        {
            "vectors": {"size": VECTOR_SIZE, "distance": "Cosine"},
            "on_disk_payload": True,
        },
    )


def index_documents(documents: list[dict[str, Any]]) -> None:
    point_id = 1
    for start in range(0, len(documents), BATCH_SIZE):
        batch = documents[start : start + BATCH_SIZE]
        vectors = embeddings([document["text"] for document in batch])
        points = []
        for document, vector in zip(batch, vectors, strict=True):
            payload = {
                **document["payload"],
                "content": document.get("content", document["text"]),
            }
            points.append({"id": point_id, "vector": vector, "payload": payload})
            point_id += 1
        request_json(
            "PUT",
            f"{QDRANT_URL}/collections/{COLLECTION}/points?wait=true",
            {"points": points},
        )
        print(f"Indexados {min(start + BATCH_SIZE, len(documents))}/{len(documents)}")


def main() -> None:
    documents = [*parse_products(), *parse_public_content()]
    recreate_collection()
    index_documents(documents)
    print(f"Colección {COLLECTION}: {len(documents)} documentos independientes")


if __name__ == "__main__":
    main()
