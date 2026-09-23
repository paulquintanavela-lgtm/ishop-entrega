#!/usr/bin/env python3
"""Clona páginas de iShop Ecuador y reescribe enlaces para que queden en local."""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.error
import urllib.request
from html import escape, unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent
ORIGIN = "https://ec.tiendasishop.com"
LOCAL_NAV_SRC = "/js/local-nav.js?v=20260923-9"
CHATBOT_WIDGET_SRC = "/chatbot/widget/chatbot-widget.js?v=20260923-2"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

CONTENT_PREFIXES = (
    "/collections/",
    "/products/",
    "/pages/",
    "/blogs/",
    "/account",
    "/cart",
    "/search",
)


def fetch(url: str) -> bytes | None:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


def asset_name(url: str) -> str:
    return Path(unescape(url).split("?", 1)[0]).name


def is_content_path(path: str) -> bool:
    if path in {"/", ""}:
        return True
    if path in {"/cart", "/search", "/account", "/account/login"}:
        return True
    return path.startswith(CONTENT_PREFIXES)


def local_page_href(path: str, fragment: str = "") -> str:
    clean = path.rstrip("/") or "/"
    if clean == "/":
        return "/" + fragment
    return f"{clean}/{fragment}"


def page_file(path: str) -> Path:
    clean = path.split("?", 1)[0].split("#", 1)[0].rstrip("/") or "/"
    if clean == "/":
        return ROOT / "index.html"
    return ROOT / clean.lstrip("/") / "index.html"


def download_theme_asset(url: str) -> str | None:
    raw = unescape(url)
    name = asset_name(raw)
    if not name:
        return None
    if name.endswith(".css"):
        dest = ROOT / "css" / "theme" / name
        public = f"/css/theme/{name}"
    elif name.endswith(".js"):
        dest = ROOT / "js" / "theme" / name
        public = f"/js/theme/{name}"
    else:
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        data = fetch(raw if raw.startswith("http") else urljoin(ORIGIN, raw))
        if data is None:
            return None
        if name.endswith(".css"):
            text = data.decode("utf-8", errors="replace")
            text = re.sub(r'url\(\s*["\']?//', 'url("https://', text)
            dest.write_text(text, encoding="utf-8")
        else:
            dest.write_bytes(data)
    return public


def rewrite_theme_assets(html: str) -> str:
    pattern = re.compile(
        r"""((?:href|src)\s*=\s*)(["'])([^"']*?/cdn/shop/t/\d+/assets/[^"']+)\2""",
        re.I,
    )

    def repl(match: re.Match[str]) -> str:
        attr, quote, url = match.group(1), match.group(2), match.group(3)
        absolute = url
        if absolute.startswith("//"):
            absolute = "https:" + absolute
        elif absolute.startswith("/"):
            absolute = ORIGIN + absolute
        local = download_theme_asset(absolute)
        if not local:
            return match.group(0)
        return f"{attr}{quote}{local}{quote}"

    return pattern.sub(repl, html)


def rewrite_page_urls(html: str) -> str:
    def repl(match: re.Match[str]) -> str:
        url = match.group(0)
        parsed = urlparse(url if "://" in url else "https:" + url)
        path = parsed.path or "/"
        if path.startswith(
            ("/cdn/", "/web-pixels", "/checkouts", "/api/", "/wpm/", "/cdn")
        ):
            if url.startswith("//"):
                return "https:" + url
            return url
        if path.startswith("/customer_authentication"):
            return "/account/"
        return local_page_href(path, ("#" + parsed.fragment) if parsed.fragment else "")

    html = re.sub(r"https?://ec\.tiendasishop\.com/[^\"'\s<>]*", repl, html)
    html = re.sub(r"(?<!:)//ec\.tiendasishop\.com/[^\"'\s<>]*", repl, html)
    return html


def extract_inline_css(html: str, path: str) -> str:
    blocks = re.findall(r"<style\b[^>]*>(.*?)</style>", html, flags=re.I | re.S)
    html = re.sub(r"<style\b[^>]*>.*?</style>", "", html, flags=re.I | re.S)
    css = "\n\n".join(block.strip() for block in blocks if block.strip())
    if css:
        slug = (path.strip("/") or "home").replace("/", "__")
        dest = ROOT / "css" / "pages" / f"{slug}.css"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(css + "\n", encoding="utf-8")
        link = f'<link rel="stylesheet" href="/css/pages/{slug}.css">'
        if "<head" in html.lower():
            html = re.sub(r"(<head\b[^>]*>)", r"\1\n    " + link, html, count=1, flags=re.I)
        else:
            html = link + html
    return html


def ensure_local_assets(html: str) -> str:
    html = html.replace('href="css/', 'href="/css/')
    html = html.replace("href='css/", "href='/css/")
    html = html.replace('src="js/', 'src="/js/')
    html = html.replace("src='js/", "src='/js/")
    html = html.replace('href="js/', 'href="/js/')
    return html


def inject_local_nav(html: str) -> str:
    tag = f'<script src="{LOCAL_NAV_SRC}"></script>'
    existing = re.compile(
        r'<script\s+src="/js/local-nav\.js(?:\?[^"]*)?"\s*></script>',
        flags=re.I,
    )
    if existing.search(html):
        return existing.sub(tag, html)
    if re.search(r"</body>", html, re.I):
        return re.sub(r"</body>", tag + "\n</body>", html, count=1, flags=re.I)
    return html + tag


def inject_chatbot_widget(html: str) -> str:
    tag = f'<script type="module" src="{CHATBOT_WIDGET_SRC}"></script>'
    existing = re.compile(
        r'<script\s+type="module"\s+src="/chatbot/widget/chatbot-widget\.js'
        r'(?:\?[^"]*)?"\s*></script>',
        flags=re.I,
    )
    if existing.search(html):
        return existing.sub(tag, html)
    if re.search(r"</body>", html, re.I):
        return re.sub(r"</body>", tag + "\n</body>", html, count=1, flags=re.I)
    return html + tag


def localize_html(html: str, path: str) -> str:
    html = re.sub(
        r'<script[^>]+src="chrome-extension://[^"]+"[^>]*></script>',
        "",
        html,
    )
    html = re.sub(r"\s*<base\b[^>]*>", "", html, count=1, flags=re.I)
    if not html.lstrip().lower().startswith("<!doctype"):
        html = "<!DOCTYPE html>\n" + html
    html = rewrite_theme_assets(html)
    html = extract_inline_css(html, path)
    html = rewrite_page_urls(html)
    html = ensure_local_assets(html)
    html = inject_local_nav(html)
    html = inject_chatbot_widget(html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html


def collect_content_paths(html: str) -> set[str]:
    found: set[str] = set()
    for raw in re.findall(r"""(?:href|action)=["']([^"']+)""", html, flags=re.I):
        url = unescape(raw).strip()
        if not url or url.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        if url.startswith("//"):
            url = "https:" + url
        if url.startswith("http"):
            parsed = urlparse(url)
            if parsed.hostname not in {"ec.tiendasishop.com", "127.0.0.1", "localhost"}:
                continue
            path = parsed.path or "/"
        elif url.startswith("/"):
            path = url.split("?", 1)[0]
        else:
            continue
        path = path.split("#", 1)[0].rstrip("/") or "/"
        if path.startswith("/customer_authentication"):
            found.add("/account")
            continue
        if is_content_path(path) and path != "/cart/add":
            found.add(path)
    return found


def title_from_path(path: str) -> str:
    slug = path.rstrip("/").split("/")[-1] or "iShop"
    slug = unescape(slug).replace("-", " ")
    return slug[:1].upper() + slug[1:]


PAGE_CONTENT: dict[str, tuple[str, str]] = {
    "/pages/preguntas-frecuentes": (
        "Preguntas frecuentes",
        """
        <h2>Información de envíos</h2>
        <p><strong>¿Cuál es el valor a pagar por gastos de envío?</strong></p>
        <p>La entrega en tiendas físicas es gratuita. Envío a domicilio gratis en compras superiores a $100. Envíos a todo el país por $6.</p>
        <h2>Pagos</h2>
        <p>Puedes pagar con Diners, Discover, American Express, Visa y MasterCard. Los diferidos aplican para tarjetas de Banco Pichincha, Diners, Guayaquil, Loja, BGR y Manabí. 12 meses sin intereses según la promoción vigente.</p>
        <p>Los productos son originales y tienen 1 año de garantía oficial del fabricante, excepto liquidación.</p>
        """,
    ),
    "/pages/promociones": (
        "Promociones",
        "<p>Revisa las ofertas destacadas de iShop Ecuador. Envío gratis desde $100 y meses sin intereses.</p>",
    ),
    "/pages/contacto": (
        "Contacto",
        "<p>Correo: tiendasishop.ec@ishopgroup.com<br>Teléfono: 099 252 7717</p>",
    ),
    "/pages/sobre-nosotros": (
        "Sobre nosotros",
        "<p>iShop Ecuador es Apple Authorized Reseller. iPhone, Mac, iPad, Watch y accesorios con garantía oficial.</p>",
    ),
    "/pages/servicio-tecnico-apple-en-ecuador": (
        "Servicio técnico",
        "<p>Servicio técnico autorizado Apple en Ecuador. Revisa también el estado de garantía en Apple.</p>",
    ),
    "/pages/tiendas-fisicas": (
        "Tiendas",
        "<p>Encuentra las tiendas iShop Ecuador. Puedes comprar online y recoger el mismo día.</p>",
    ),
    "/pages/ventas-corporativas": (
        "Ventas corporativas",
        "<p>Soluciones Apple para empresas, educación y home office.</p>",
    ),
    "/pages/beneficios-ishop": (
        "Beneficios iShop",
        "<p>Envío gratis desde $100, 12 meses sin intereses y garantía oficial de 1 año.</p>",
    ),
    "/pages/politica-de-privacidad": (
        "Política de privacidad",
        "<p>Copia local informativa. Consulta el texto legal completo en la tienda cuando esté disponible.</p>",
    ),
    "/pages/terminos-y-condiciones": (
        "Términos y condiciones",
        "<p>Copia local informativa de los términos de la tienda iShop Ecuador.</p>",
    ),
    "/pages/politicas-de-devolucion-cambio-garantia": (
        "Devolución y garantía",
        "<p>Puedes cambiar o devolver un producto según la política de devolución. Garantía oficial de 1 año, excepto liquidación.</p>",
    ),
    "/cart": (
        "Carrito",
        "<p>Tu carrito está vacío.</p><p><a class='btn btn--primary' href='/'>Comenzar a comprar</a></p>",
    ),
    "/search": (
        "Buscar",
        """
        <form class="search" action="/search" method="get">
          <input class="input w-full" type="search" name="q" placeholder="¿Qué estás buscando?">
        </form>
        <p class="mt-6">Escribe en el buscador del header para explorar la copia local.</p>
        """,
    ),
    "/account": (
        "Cuenta",
        "<p>Esta es una copia local. El inicio de sesión de Shopify no está disponible aquí.</p>",
    ),
}


def load_shell() -> tuple[str, str]:
    html = (ROOT / "index.html").read_text(encoding="utf-8", errors="replace")
    html = neutralize_external_shop_links(html)
    header, rest = html.split("<!-- END sections: header-group -->", 1)
    _, footer = rest.split("<!-- BEGIN sections: footer-group -->", 1)
    return header, "<!-- BEGIN sections: footer-group -->" + footer


def neutralize_external_shop_links(html: str) -> str:
    for host in (
        "https://co.tiendasishop.com/",
        "https://co.tiendasishop.com",
        "https://cr.tiendasishop.com/",
        "https://cr.tiendasishop.com",
        "https://sv.tiendasishop.com/",
        "https://sv.tiendasishop.com",
        "https://pa.tiendasishop.com/",
        "https://pa.tiendasishop.com",
        "https://pe.tiendasishop.com/",
        "https://pe.tiendasishop.com",
        "https://tips.tiendasishop.com/",
        "https://tips.tiendasishop.com",
    ):
        html = html.replace(f'href="{host}"', 'href="/"')
        html = html.replace(f"href='{host}'", "href='/'")
    return html


def related_links(path: str) -> list[tuple[str, str]]:
    index = (ROOT / "index.html").read_text(encoding="utf-8", errors="replace")
    links: list[tuple[str, str]] = []
    seen: set[str] = set()
    keywords = [part for part in path.split("/") if part and part not in {"collections", "products", "pages"}]
    for match in re.finditer(
        r"""<a\b[^>]*href=["'](/[^"']+)["'][^>]*>(.*?)</a>""",
        index,
        flags=re.I | re.S,
    ):
        href = unescape(match.group(1)).split("?", 1)[0]
        text = re.sub(r"<[^>]+>", "", match.group(2))
        text = re.sub(r"\s+", " ", text).strip()
        if not text or href in seen or len(text) > 80:
            continue
        if any(key in href for key in keywords) or any(key in href for key in path.split("-")):
            seen.add(href)
            links.append((href if href.endswith("/") or href == "/" else href, text))
        if len(links) >= 16:
            break
    return links


def generate_local_page(path: str) -> Path:
    dest = page_file(path)
    title, body = PAGE_CONTENT.get(path, (title_from_path(path), ""))
    if not body:
        cards = related_links(path)
        if cards:
            items = "".join(
                f'<li class="mb-4"><a class="link" href="{href}">{text}</a></li>'
                for href, text in cards
            )
            body = f"<p>Explora esta sección de la copia local.</p><ul>{items}</ul>"
        else:
            body = "<p>Página de la copia local de iShop Ecuador.</p>"

    header, footer = load_shell()
    header = re.sub(
        r"<title>.*?</title>",
        f"<title>{title} | iShop Ecuador</title>",
        header,
        count=1,
        flags=re.I | re.S,
    )
    page = (
        f"{header}<!-- END sections: header-group -->"
        f'<main id="main-content"><section class="section">'
        f'<div class="container" style="padding:48px 0 80px;max-width:960px;">'
        f"<h1 class=\"mb-6\">{title}</h1>{body}"
        f'<p style="margin-top:32px;"><a href="/">Volver al inicio</a></p>'
        f"</div></section></main>"
        f"{footer}"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page, encoding="utf-8")
    return dest


def clone_page(path: str) -> Path | None:
    dest = page_file(path)
    if dest.exists() and dest != ROOT / "index.html":
        return dest
    if path in {"/", ""}:
        return ROOT / "index.html"
    return generate_local_page(path)


def write_account_stub() -> None:
    dest = ROOT / "account" / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cuenta | iShop Ecuador (copia local)</title>
  <link rel="stylesheet" href="/css/theme/main.css">
  <link rel="stylesheet" href="/css/inline.css">
</head>
<body class="dom-loaded">
  <main class="container" style="max-width:720px;margin:80px auto;padding:24px;">
    <h1>Iniciar sesión</h1>
    <p>Esta es una copia local. El login original de Shopify no está disponible aquí.</p>
    <p><a href="/">Volver al inicio</a></p>
  </main>
  <script src="/js/local-nav.js"></script>
</body>
</html>
""",
        encoding="utf-8",
    )


def rewrite_existing_index() -> None:
    index = ROOT / "index.html"
    html = index.read_text(encoding="utf-8", errors="replace")
    html = localize_html(html, "/")
    index.write_text(html, encoding="utf-8")


def parse_catalog_products() -> list[dict[str, object]]:
    catalog = ROOT / "chatbot" / "knowledge" / "catalogo-productos.md"
    if not catalog.exists():
        raise FileNotFoundError(f"No se encontró el catálogo: {catalog}")

    products: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    reading_variants = False

    for raw_line in catalog.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            if current is not None:
                products.append(current)
            current = {
                "name": line[3:].strip(),
                "url": "",
                "type": "",
                "brand": "",
                "tags": "",
                "description": "",
                "variants": [],
            }
            reading_variants = False
            continue

        if current is None:
            continue
        if line == "- Variantes:":
            reading_variants = True
            continue

        field_match = re.match(
            r"^- (URL|Tipo|Marca|Etiquetas|Descripción):\s*(.*)$",
            line,
        )
        if field_match:
            field_name = {
                "URL": "url",
                "Tipo": "type",
                "Marca": "brand",
                "Etiquetas": "tags",
                "Descripción": "description",
            }[field_match.group(1)]
            current[field_name] = field_match.group(2).strip()
            reading_variants = False
            continue

        if reading_variants and line.startswith("- "):
            variants = current["variants"]
            if isinstance(variants, list):
                variants.append(line[2:].strip())

    if current is not None:
        products.append(current)

    image_catalog = ROOT / "chatbot" / "knowledge" / "product-images.json"
    image_by_handle: dict[str, str] = {}
    if image_catalog.exists():
        raw_images = json.loads(image_catalog.read_text(encoding="utf-8"))
        if isinstance(raw_images, dict):
            image_by_handle = {
                str(handle): str(image_url)
                for handle, image_url in raw_images.items()
            }

    valid_products = [
        product
        for product in products
        if urlparse(str(product["url"])).path.startswith("/products/")
    ]
    for product in valid_products:
        handle = urlparse(str(product["url"])).path.rstrip("/").split("/")[-1]
        product["image"] = image_by_handle.get(handle, "")
    return valid_products


def variant_parts(variant: str) -> tuple[str, str, str]:
    match = re.match(
        r"^(.*?):\s*(\$[0-9]+(?:\.[0-9]+)?)(?:\s+\((.*?)\))?$",
        variant,
    )
    if not match:
        return variant, "", ""
    return match.group(1), match.group(2), match.group(3) or ""


def product_starting_price(variants: list[str]) -> str:
    prices: list[float] = []
    for variant in variants:
        match = re.search(r"\$([0-9]+(?:\.[0-9]+)?)", variant)
        if match:
            prices.append(float(match.group(1)))
    if not prices:
        return "Precio no disponible"
    return f"Desde ${min(prices):,.2f}"


def sized_image_url(image_url: object, width: int) -> str:
    source = str(image_url).strip()
    if not source:
        return ""
    separator = "&" if "?" in source else "?"
    return f"{source}{separator}width={width}"


def render_product_body(product: dict[str, object]) -> str:
    name = escape(str(product["name"]))
    product_type = escape(str(product["type"]) or "Producto")
    brand = escape(str(product["brand"]) or "iShop")
    description = escape(str(product["description"]))
    source_url = escape(str(product["url"]), quote=True)
    variants = [str(item) for item in product["variants"]]
    starting_price = escape(product_starting_price(variants))
    image_url = sized_image_url(product.get("image", ""), 1000)
    if image_url:
        visual_content = (
            f'<img class="local-product__image" src="{escape(image_url, quote=True)}" '
            f'alt="{name}" loading="eager">'
        )
    else:
        visual_content = (
            f'<span class="local-product__brand">{brand}</span>'
            f'<span class="local-product__device">{product_type}</span>'
        )

    raw_tags = str(product["tags"])
    tags = [] if raw_tags == "Sin etiquetas" else [
        tag.strip() for tag in raw_tags.split(",") if tag.strip()
    ]
    tag_html = "".join(
        f'<span class="local-product__tag">{escape(tag)}</span>' for tag in tags
    )

    variant_items: list[str] = []
    for variant in variants:
        option, price, availability = variant_parts(variant)
        availability_html = (
            f'<span class="local-product__availability">{escape(availability)}</span>'
            if availability
            else ""
        )
        variant_items.append(
            '<li class="local-product__variant">'
            f'<span class="local-product__variant-name">{escape(option)}</span>'
            f'<strong class="local-product__variant-price">{escape(price)}</strong>'
            f"{availability_html}</li>"
        )
    variants_html = "".join(variant_items) or (
        '<li class="local-product__variant">No hay variantes publicadas.</li>'
    )

    return f"""
<main id="main-content" class="local-product">
  <div class="local-product__container">
    <nav class="local-product__breadcrumb" aria-label="Migas de pan">
      <a href="/">Inicio</a><span aria-hidden="true">/</span>
      <a href="/collections/all/">Productos</a><span aria-hidden="true">/</span>
      <span>{name}</span>
    </nav>

    <section class="local-product__hero">
      <div class="local-product__visual">
        {visual_content}
      </div>
      <div class="local-product__summary">
        <p class="local-product__eyebrow">{brand} · {product_type}</p>
        <h1>{name}</h1>
        <p class="local-product__price">{starting_price}</p>
        <div class="local-product__tags">{tag_html}</div>
        <p class="local-product__notice">
          Precio y disponibilidad tomados del catálogo público de demostración.
          Pueden cambiar.
        </p>
        <div class="local-product__actions">
          <a class="local-product__button" href="{source_url}" target="_blank"
             rel="noopener noreferrer">Ver ficha original</a>
          <a class="local-product__secondary" href="/collections/all/">
            Ver más productos
          </a>
        </div>
      </div>
    </section>

    <section class="local-product__section" aria-labelledby="description-title">
      <h2 id="description-title">Descripción</h2>
      <p>{description}</p>
    </section>

    <section class="local-product__section" aria-labelledby="variants-title">
      <h2 id="variants-title">Opciones y precios publicados</h2>
      <ul class="local-product__variants">{variants_html}</ul>
    </section>
  </div>
</main>
"""


def render_catalog_product_pages() -> int:
    products = parse_catalog_products()
    header, footer = load_shell()
    stylesheet = '<link rel="stylesheet" href="/css/local-product.css">'
    if stylesheet not in header:
        header = re.sub(
            r"</head>",
            f"  {stylesheet}\n</head>",
            header,
            count=1,
            flags=re.I,
        )

    generated = 0
    for product in products:
        product_url = str(product["url"])
        path = urlparse(product_url).path.rstrip("/")
        if not path.startswith("/products/"):
            continue

        title = escape(str(product["name"]))
        page_header = re.sub(
            r"<title>.*?</title>",
            f"<title>{title} | iShop Ecuador</title>",
            header,
            count=1,
            flags=re.I | re.S,
        )
        page = (
            f"{page_header}<!-- END sections: header-group -->"
            f"{render_product_body(product)}"
            f"{footer}"
        )
        destination = page_file(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page, encoding="utf-8")
        generated += 1

    return generated


COLLECTION_TITLES = {
    "all": "Todos los productos",
    "todos-los-mac": "Todos los Mac",
    "todos-los-ipad": "Todos los iPad",
    "todos-los-iphone": "Todos los iPhone",
    "todos-los-apple-watch": "Todos los Apple Watch",
    "macbook-air": "MacBook Air",
    "macbook-pro": "MacBook Pro",
    "mac-mini": "Mac mini",
    "ipad-air": "iPad Air",
    "ipad-pro": "iPad Pro",
    "airpods": "AirPods",
    "airtag": "AirTag",
    "apple-tv": "Apple TV",
    "parlantes": "Parlantes",
    "audifonos": "Audífonos",
    "cargadores": "Cargadores",
    "todas-las-promociones": "Productos destacados",
}


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def is_primary_device(product: dict[str, object]) -> bool:
    name = normalize_text(product["name"])
    prefixes = (
        "iphone ",
        "ipad ",
        "apple watch ",
        "macbook ",
        "imac ",
        "mac mini ",
        "airpods ",
        "apple tv ",
    )
    return name.startswith(prefixes)


def product_matches_collection(
    product: dict[str, object],
    handle: str,
) -> bool:
    name = normalize_text(product["name"])
    product_type = normalize_text(product["type"])
    brand = normalize_text(product["brand"])
    tags = normalize_text(product["tags"])
    searchable = " ".join((name, product_type, brand, tags))

    if handle == "all":
        return True
    if handle == "todos-los-mac":
        return any(term in name for term in ("macbook", "imac", "mac mini"))
    if handle == "todos-los-ipad":
        return name.startswith("ipad ")
    if handle == "todos-los-iphone":
        return name.startswith("iphone ")
    if handle == "todos-los-apple-watch":
        return name.startswith("apple watch ")
    if handle == "todas-las-promociones":
        return is_primary_device(product)
    if handle == "parlantes":
        return any(term in searchable for term in ("parlante", "soundlink", "bose s1"))
    if handle == "audifonos":
        return any(
            term in searchable
            for term in ("audifono", "airpods", "earbuds", "earpods", "major v")
        )
    if handle == "cargadores":
        return any(
            term in searchable
            for term in ("cargador", "adaptador de corriente", "base de carga")
        )

    accessory_target = re.fullmatch(r"accesorios-para-(.+)", handle)
    if accessory_target:
        target = normalize_text(accessory_target.group(1))
        target = {
            "apple watch": "apple watch",
            "airpods": "airpods",
            "iphone": "iphone",
            "ipad": "ipad",
            "mac": "mac",
            "gear4": "gear4",
        }.get(target, target)
        return target in searchable and not is_primary_device(product)

    brand_collection = re.fullmatch(r"accesorios-de-(.+)", handle)
    if brand_collection:
        target_brand = normalize_text(brand_collection.group(1))
        if target_brand == "apple":
            return brand == "apple" and not is_primary_device(product)
        return brand == target_brand

    exact_phrases = {
        "macbook-air": "macbook air",
        "macbook-pro": "macbook pro",
        "mac-mini": "mac mini",
        "ipad-air": "ipad air",
        "ipad-pro": "ipad pro",
        "airpods": "airpods",
        "airtag": "airtag",
        "apple-tv": "apple tv",
    }
    if handle in exact_phrases:
        return exact_phrases[handle] in name

    words = [
        word
        for word in normalize_text(handle.replace("-", " ")).split()
        if word not in {"los", "las", "de", "del", "y", "para"}
    ]
    return bool(words) and all(word in searchable for word in words)


def collection_title(handle: str) -> str:
    return COLLECTION_TITLES.get(handle, title_from_path(handle))


def render_collection_card(product: dict[str, object]) -> str:
    name = escape(str(product["name"]))
    product_type = escape(str(product["type"]) or "Producto")
    path = urlparse(str(product["url"])).path.rstrip("/") + "/"
    variants = [str(item) for item in product["variants"]]
    price = escape(product_starting_price(variants))
    image_url = sized_image_url(product.get("image", ""), 600)
    if image_url:
        visual = (
            '<div class="local-collection__visual">'
            f'<img src="{escape(image_url, quote=True)}" alt="{name}" loading="lazy">'
            "</div>"
        )
    else:
        visual = (
            '<div class="local-collection__visual" aria-hidden="true">'
            f"<span>{product_type}</span></div>"
        )
    return (
        '<article class="local-collection__card">'
        f"{visual}"
        '<div class="local-collection__card-body">'
        f"<p>{product_type}</p><h2><a href=\"{escape(path, quote=True)}\">{name}</a></h2>"
        f'<strong>{price}</strong>'
        f'<a class="local-collection__link" href="{escape(path, quote=True)}">'
        "Ver detalles</a></div></article>"
    )


def write_catalog_listing(
    title: str,
    products: list[dict[str, object]],
    destination: Path,
    header: str,
    footer: str,
) -> None:
    matches = sorted(
        products,
        key=lambda product: (
            not is_primary_device(product),
            normalize_text(product["name"]),
        ),
    )
    page_header = re.sub(
        r"<title>.*?</title>",
        f"<title>{escape(title)} | iShop Ecuador</title>",
        header,
        count=1,
        flags=re.I | re.S,
    )
    cards = "".join(render_collection_card(product) for product in matches)
    if not cards:
        cards = (
            '<div class="local-collection__empty">'
            "<h2>No hay productos publicados en esta categoría.</h2>"
            "<p>El catálogo local se actualiza desde la información pública de iShop.</p>"
            '<a href="/collections/all/">Ver todos los productos</a></div>'
        )

    body = f"""
<main id="main-content" class="local-collection">
  <div class="local-collection__container">
    <nav class="local-collection__breadcrumb" aria-label="Migas de pan">
      <a href="/">Inicio</a><span aria-hidden="true">/</span><span>{escape(title)}</span>
    </nav>
    <header class="local-collection__header">
      <p>Catálogo público de demostración</p>
      <h1>{escape(title)}</h1>
      <span>{len(matches)} productos encontrados</span>
    </header>
    <section class="local-collection__grid" aria-label="{escape(title)}">
      {cards}
    </section>
  </div>
</main>
"""
    page = f"{page_header}<!-- END sections: header-group -->{body}{footer}"
    page = "\n".join(line.rstrip() for line in page.splitlines()) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page, encoding="utf-8")


def catalog_shell() -> tuple[str, str]:
    header, footer = load_shell()
    stylesheet = '<link rel="stylesheet" href="/css/local-collection.css">'
    if stylesheet not in header:
        header = re.sub(
            r"</head>",
            f"  {stylesheet}\n</head>",
            header,
            count=1,
            flags=re.I,
        )
    return header, footer


def render_catalog_collection_pages() -> int:
    products = parse_catalog_products()
    collections_root = ROOT / "collections"
    handles = {
        path.name
        for path in collections_root.iterdir()
        if path.is_dir()
    }

    header, footer = catalog_shell()

    generated = 0
    for handle in sorted(handles):
        matches = [
            product
            for product in products
            if product_matches_collection(product, handle)
        ]
        title = collection_title(handle)
        destination = collections_root / handle / "index.html"
        write_catalog_listing(title, matches, destination, header, footer)
        generated += 1

    return generated


CATALOG_MENU_PAGES: dict[str, tuple[str, tuple[str, ...]]] = {
    "airpods": ("AirPods", ("airpods",)),
    "parlantes-y-audifonos": ("Audio", ("parlantes", "audifonos")),
    "todos-los-accesorios": ("Todos los accesorios", ("accessories",)),
    "accesorios-para-mac": ("Accesorios para Mac", ("accesorios-para-mac",)),
    "accesorios-para-iphone": ("Accesorios para iPhone", ("accesorios-para-iphone",)),
    "accesorios-para-ipad": ("Accesorios para iPad", ("accesorios-para-ipad",)),
    "accesorios-para-apple-watch": (
        "Accesorios para Apple Watch",
        ("accesorios-para-apple-watch",),
    ),
    "compara-los-modelos-de-mac": ("Modelos de Mac", ("todos-los-mac",)),
    "compara-los-modelos-de-ipad": ("Modelos de iPad", ("todos-los-ipad",)),
    "compara-los-modelos-de-iphone": ("Modelos de iPhone", ("todos-los-iphone",)),
    "compara-los-modelos-de-watch": (
        "Modelos de Apple Watch",
        ("todos-los-apple-watch",),
    ),
    "compara-los-modelos-de-airpods": ("Modelos de AirPods", ("airpods",)),
    "entretenimiento-apple": (
        "Entretenimiento Apple",
        ("apple-tv", "airpods", "parlantes", "audifonos"),
    ),
    "los-mejores-productos-nco": (
        "Productos NCO",
        ("accesorios-de-nco",),
    ),
    "creativos-y-pro": (
        "Soluciones para creativos y profesionales",
        ("todos-los-mac", "todos-los-ipad"),
    ),
    "estudio-y-academia": (
        "Soluciones para estudio y academia",
        ("todos-los-mac", "todos-los-ipad"),
    ),
    "negocios-y-home-office": (
        "Soluciones para negocios y home office",
        ("todos-los-mac", "todos-los-ipad"),
    ),
}


def render_catalog_menu_pages() -> int:
    products = parse_catalog_products()
    header, footer = catalog_shell()

    for slug, (title, handles) in CATALOG_MENU_PAGES.items():
        if handles == ("accessories",):
            matches = [product for product in products if not is_primary_device(product)]
        else:
            matches = [
                product
                for product in products
                if any(
                    product_matches_collection(product, handle)
                    for handle in handles
                )
            ]
        write_catalog_listing(
            title,
            matches,
            ROOT / "pages" / slug / "index.html",
            header,
            footer,
        )

    return len(CATALOG_MENU_PAGES)


def refresh_local_nav_references() -> int:
    updated = 0
    for path in ROOT.rglob("index.html"):
        html = path.read_text(encoding="utf-8", errors="replace")
        refreshed = inject_local_nav(html)
        refreshed = inject_chatbot_widget(refreshed)
        if refreshed == html:
            continue
        path.write_text(refreshed, encoding="utf-8")
        updated += 1
    return updated


if __name__ == "__main__":
    product_total = render_catalog_product_pages()
    collection_total = render_catalog_collection_pages()
    menu_page_total = render_catalog_menu_pages()
    navigation_total = refresh_local_nav_references()
    print(
        f"Páginas de producto generadas: {product_total}; "
        f"colecciones generadas: {collection_total}; "
        f"páginas de menú generadas: {menu_page_total}; "
        f"referencias de navegación actualizadas: {navigation_total}"
    )
