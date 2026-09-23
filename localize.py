#!/usr/bin/env python3
"""Clona páginas de iShop Ecuador y reescribe enlaces para que queden en local."""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent
ORIGIN = "https://ec.tiendasishop.com"
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
    tag = '<script src="/js/local-nav.js"></script>'
    if "js/local-nav.js" in html:
        return html
    if re.search(r"</body>", html, re.I):
        return re.sub(r"</body>", tag + "\n</body>", html, count=1, flags=re.I)
    return html + tag


def inject_chatbot_widget(html: str) -> str:
    tag = '<script type="module" src="/chatbot/widget/chatbot-widget.js"></script>'
    if "chatbot/widget/chatbot-widget.js" in html:
        return html
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
