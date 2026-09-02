import os
import re
import asyncio
import json
import html as html_lib
from urllib.parse import urljoin, urlparse
from typing import Tuple

import backend.utils as utils
from backend.config import settings
from bs4 import BeautifulSoup
from playwright.async_api import TimeoutError
from backend.logging import logger


async def extrair_dados(page, url):
    logger.info(f"Iniciando extração multi-site: {url}")
    try:
        if page.url != url:
            await page.goto(url, timeout=settings.timeout_carregamento, wait_until="domcontentloaded")
    except TimeoutError:
        logger.warning(f"Timeout carregando: {url}")

    try:
        await page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass

    await asyncio.sleep(2)
    try:
        await utils.scroll_humano(page)
    except Exception:
        pass

    html = await page.content()
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    structured = _extrair_dados_estruturados(soup, url)
    listing_text = structured.get("text") or text

    titulo = structured.get("titulo") or _extrair_titulo(soup, listing_text)
    descricao = structured.get("descricao") or _extrair_descricao(soup, listing_text)
    preco = structured.get("preco") or _extrair_preco(listing_text)
    quartos, banheiros, garagem = _extrair_comodos(listing_text)
    quartos = structured.get("quartos", quartos)
    banheiros = structured.get("banheiros", banheiros)
    garagem = structured.get("garagem", garagem)
    area = structured.get("area") or _extrair_area(listing_text)
    endereco = structured.get("endereco") or _extrair_endereco(soup, listing_text)
    fotos = await _extrair_fotos(
        page,
        soup,
        url,
        preferred_urls=structured.get("fotos") or None,
    )

    dados = {
        "titulo": titulo or "Imóvel",
        "descricao": descricao,
        "preco": preco,
        "endereco": endereco,
        "quartos": quartos,
        "banheiros": banheiros,
        "garagem": garagem,
        "area": area,
        "url": url,
        "fotos": fotos,
    }
    logger.info(f"EXTRAÇÃO FINALIZADA: Preço {preco}, Quartos {quartos}, Fotos {len(fotos)}")
    return dados


def _flatten_json(value):
    if isinstance(value, list):
        for item in value:
            yield from _flatten_json(item)
    elif isinstance(value, dict):
        yield value
        for item in value.values():
            if isinstance(item, (dict, list)):
                yield from _flatten_json(item)


def _clean_url(value: str) -> str:
    parsed = urlparse(value)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/").lower()


def _as_number(value):
    if isinstance(value, (int, float)):
        return value
    if not value:
        return 0
    match = re.search(r"\d+(?:[.,]\d+)?", str(value))
    if not match:
        return 0
    raw = match.group(0)
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif raw.count(".") > 1:
        raw = raw.replace(".", "")
    return float(raw)


def _property_values(entity):
    values = {}
    properties = entity.get("additionalProperty") or entity.get("additionalProperties") or []
    if isinstance(properties, dict):
        properties = [properties]
    for prop in properties:
        if isinstance(prop, dict) and prop.get("name"):
            values[str(prop["name"]).lower()] = prop.get("value")
    return values


def _extrair_dados_estruturados(soup, url):
    """Extract the listing entity that matches the requested URL from JSON-LD."""
    requested = _clean_url(url)
    entities = []
    for script in soup.select("script[type='application/ld+json']"):
        try:
            payload = json.loads(script.string or script.get_text())
            entities.extend(_flatten_json(payload))
        except (json.JSONDecodeError, TypeError):
            continue

    candidates = []
    for entity in entities:
        entity_url = entity.get("url") or entity.get("@id")
        item = entity.get("itemOffered")
        if isinstance(item, dict):
            merged = dict(item)
            merged.update({key: value for key, value in entity.items() if key not in merged})
            entity = merged
            entity_url = entity.get("url") or entity.get("@id")
        if entity_url and _clean_url(str(entity_url)) == requested:
            candidates.append(entity)

    candidates = [
        entity for entity in candidates
        if entity.get("name") or entity.get("description") or entity.get("image")
    ]

    # Some portals publish one complete Product entity without a URL and a
    # second partial node with the page URL. Rank both and keep the richest.
    products = []
    for entity in entities:
        offers = entity.get("offers") or {}
        has_price = bool(entity.get("price")) or (
            isinstance(offers, dict) and bool(offers.get("price"))
        )
        if entity.get("name") and has_price and entity.get("image"):
            products.append(entity)
    candidates.extend(products)
    if not candidates:
        return {}

    entity = max(
        candidates,
        key=lambda item: sum(bool(item.get(key)) for key in ("name", "description", "image", "offers", "price")),
    )
    offers = entity.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    properties = _property_values(entity)
    address = entity.get("address") or {}
    if isinstance(address, str):
        address_text = address
    else:
        address_text = ", ".join(str(address.get(key)) for key in ("streetAddress", "addressLocality", "addressRegion") if address.get(key))

    images = entity.get("image") or []
    if isinstance(images, str):
        images = [images]
    images = [urljoin(url, image) for image in images if isinstance(image, str)]
    entity_text = html_lib.unescape(" ".join(str(value) for value in (entity.get("name"), entity.get("description")) if value))
    bedrooms = int(_as_number(entity.get("numberOfBedrooms") or properties.get("quartos") or properties.get("dormitórios"))) or _extrair_comodos(entity_text)[0]
    bathrooms = int(_as_number(entity.get("numberOfBathroomsTotal") or entity.get("numberOfBathrooms") or properties.get("banheiros"))) or _extrair_comodos(entity_text)[1]
    parking = 0
    features = entity.get("amenityFeature") or []
    if isinstance(features, dict):
        features = [features]
    for feature in features:
        if isinstance(feature, dict) and any(word in str(feature.get("name", "")).lower() for word in ("garagem", "vaga", "parking")):
            parking = int(_as_number(feature.get("value")))
    if not parking:
        parking = int(_as_number(properties.get("garagem") or properties.get("vagas"))) or _extrair_comodos(entity_text)[2]

    area = entity.get("floorSize") or entity.get("area") or entity.get("floorArea") or properties.get("área total") or properties.get("área útil") or properties.get("area") or _extrair_area(entity_text)
    if isinstance(area, dict):
        area = area.get("value")

    return {
        "titulo": entity.get("name") or entity.get("description") or "",
        "descricao": entity.get("description") or "",
        "preco": _as_number(offers.get("price") or entity.get("price")),
        "quartos": bedrooms,
        "banheiros": bathrooms,
        "garagem": parking,
        "area": int(_as_number(area)),
        "endereco": address_text,
        "fotos": list(dict.fromkeys(images)),
        "text": html_lib.unescape(" ".join(str(value) for value in (entity.get("name"), entity.get("description"), address_text))),
    }


def _extrair_titulo(soup, text: str) -> str:
    for selector in ["meta[property='og:title']", "meta[name='twitter:title']", "h1", "h2"]:
        tag = soup.select_one(selector)
        if tag:
            value = tag.get("content") or tag.get_text(" ", strip=True)
            if value:
                return re.sub(r"\s+", " ", value).strip()[:300]

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if title:
        return re.sub(r"\s+", " ", title).strip()[:300]
    return text[:300]


def _extrair_descricao(soup, text: str) -> str:
    meta_desc = soup.select_one("meta[name='description']")
    if meta_desc and meta_desc.get("content"):
        return re.sub(r"\s+", " ", meta_desc.get("content")).strip()[:5000]

    candidates = soup.select("p, li, article, div")
    for el in candidates:
        txt = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
        if len(txt) < 80:
            continue
        lowered = txt.lower()
        if any(k in lowered for k in ["quartos", "banheiros", "m²", "dormitórios", "área", "garagem", "imóvel"]):
            return txt[:5000]

    return text[:5000]


def _extrair_preco(text: str):
    patterns = [
        r"R\$\s*([\d\.\s]+,\d{2})",
        r"(?:valor|preço|price)[^\d]{0,20}R\$\s*([\d\.\s]+,\d{2})",
        r"([\d\.\s]+)\s*mil",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            val = match.group(1).replace(".", "").replace(" ", "").replace(",", ".")
            try:
                return float(val)
            except ValueError:
                pass
    return 0


def _extrair_comodos(text: str) -> Tuple[int, int, int]:
    quartos = banheiros = garagem = 0

    q = re.search(r"(\d+)\s*(?:quartos?|dormit[óo]rios?|bedrooms?|bedroom)", text, re.I)
    if q:
        quartos = int(q.group(1))

    b = re.search(r"(\d+)\s*(?:banheiros?|bathrooms?|bathroom)", text, re.I)
    if b:
        banheiros = int(b.group(1))

    g = re.search(r"(\d+)\s*(?:vagas?|garagens?|parking|carports?)", text, re.I)
    if g:
        garagem = int(g.group(1))

    return quartos, banheiros, garagem


def _extrair_area(text: str) -> int:
    match = re.search(r"(\d{2,}(?:[.,]\d+)?)\s*(?:m²|m2|metros quadrados|m\s*quadrados|área)", text, re.I)
    if match:
        return int(_as_number(match.group(1)))
    return 0


def _extrair_endereco(soup, text: str) -> str:
    for selector in ["meta[property='og:street-address']", "meta[name='geo.placename']", "address", ".address", "span[itemprop='addressLocality']"]:
        tag = soup.select_one(selector)
        if tag:
            value = tag.get("content") or tag.get_text(" ", strip=True)
            if value:
                return re.sub(r"\s+", " ", value).strip()[:500]

    candidates = ["bairro", "rua", "logradouro", "endereço", "cidade", "estado"]
    for phrase in candidates:
        idx = text.lower().find(phrase.lower())
        if idx != -1:
            snippet = text[max(0, idx - 60): idx + 180]
            if snippet:
                return re.sub(r"\s+", " ", snippet).strip()[:500]
    return ""


async def _extrair_fotos(page, soup, url_imovel, preferred_urls=None):
    imagens = []
    try:
        if preferred_urls:
            imagens.extend(preferred_urls)

        for tag in soup.select("meta[property='og:image'], meta[name='twitter:image']"):
            image_url = tag.get("content")
            if image_url:
                imagens.append(urljoin(url_imovel, image_url))

        for script in soup.find_all("script"):
            for image_url in re.findall(r"https?://[^\"'\\s]+?\.(?:jpe?g|png|webp)(?:\?[^\"'\\s]+)?", script.get_text(), re.I):
                imagens.append(image_url)

        # JSON-LD costuma trazer apenas a capa; complemente com a galeria HTML.
        for tag in soup.find_all(["img", "source"]):
            for attr in ["src", "data-src", "data-lazy-src", "srcset"]:
                value = tag.get(attr)
                if not value:
                    continue
                urls = [part.strip().split(" ")[0] for part in str(value).split(",")]
                for image_url in urls:
                    if image_url.startswith("http") and not any(k in image_url.lower() for k in ["logo", "avatar", "icon", "badge"]):
                        imagens.append(image_url)

        for _ in range(12):
            try:
                cards = await page.query_selector_all("img")
                for card in cards:
                    src = await card.get_attribute("src") or await card.get_attribute("data-src")
                    if src and src.startswith("http") and not any(k in src.lower() for k in ["logo", "avatar", "icon", "badge"]):
                        imagens.append(src)
                await page.mouse.wheel(0, 500)
                await asyncio.sleep(0.6)
            except Exception:
                break

        imagens = [img.split("?")[0] for img in imagens if img and not any(k in img.lower() for k in ("logo", "avatar", "icon", "badge"))]
        imagens = list(dict.fromkeys(imagens))

        # O Render gratuito não possui disco persistente. Mantemos as URLs no
        # Neon e baixamos os arquivos somente durante a publicação.
        return imagens[:12]

    except Exception as e:
        logger.warning(f"Erro fotos multi-site: {e}")
        return []
