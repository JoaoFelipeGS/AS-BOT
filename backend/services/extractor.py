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
            await page.goto(url, timeout=35000, wait_until="domcontentloaded")
    except TimeoutError:
        logger.warning(f"Timeout carregando: {url}; usando o HTML disponível")

    try:
        await page.wait_for_load_state("networkidle", timeout=3000)
    except Exception:
        pass

    await asyncio.sleep(0.5)
    try:
        for _ in range(3):
            await page.mouse.wheel(0, 700)
            await asyncio.sleep(0.35)
    except Exception:
        pass

    try:
        html = await page.content()
    except Exception as error:
        logger.warning(f"Página encerrada antes da leitura: {url} ({error.__class__.__name__})")
        return None
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    structured = _extrair_dados_estruturados(soup, url)
    # JSON-LD pode conter apenas parte do anúncio; mantenha o texto visível
    # disponível para completar campos ausentes nesse bloco estruturado.
    listing_text = " ".join(filter(None, (structured.get("text"), text)))

    titulo = structured.get("titulo") or _extrair_titulo(soup, listing_text)
    descricao = structured.get("descricao") or _extrair_descricao(soup, listing_text)
    preco = structured.get("preco") or _extrair_preco(listing_text)
    room_text = " ".join(filter(None, (titulo, descricao, url, structured.get("text"))))
    quartos, banheiros, garagem = _extrair_comodos(room_text)
    visible_rooms = _extrair_comodos(text)
    quartos = _valid_count(quartos) or visible_rooms[0] or _valid_count(structured.get("quartos"))
    banheiros = _valid_count(banheiros) or visible_rooms[1] or _valid_count(structured.get("banheiros"))
    garagem = _valid_count(garagem) or visible_rooms[2] or _valid_count(structured.get("garagem"))
    area = _extrair_area(room_text) or structured.get("area") or _extrair_area(text)
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
    for campo in ("titulo", "descricao", "quartos", "banheiros", "garagem", "area", "fotos"):
        valor = dados.get(campo)
        if valor in (None, "", 0, []):
            logger.warning(f"Campo '{campo}' não encontrado ou vazio em {url}")
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


def _valid_count(value, maximum=20):
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return number if 0 < number <= maximum else 0


def _property_value(properties, *names):
    normalized = {
        re.sub(r"[^a-z0-9]", "", key.lower()): value
        for key, value in properties.items()
    }
    for name in names:
        value = normalized.get(re.sub(r"[^a-z0-9]", "", name.lower()))
        if value not in (None, ""):
            return value
    return None


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
    bedrooms = int(_as_number(entity.get("numberOfBedrooms") or entity.get("numberOfRooms") or _property_value(properties, "quartos", "dormitorios", "bedrooms", "rooms"))) or _extrair_comodos(entity_text)[0]
    bathrooms = int(_as_number(entity.get("numberOfBathroomsTotal") or entity.get("numberOfBathrooms") or _property_value(properties, "banheiros", "bathrooms"))) or _extrair_comodos(entity_text)[1]
    parking = 0
    features = entity.get("amenityFeature") or []
    if isinstance(features, dict):
        features = [features]
    for feature in features:
        if isinstance(feature, dict) and any(word in str(feature.get("name", "")).lower() for word in ("garagem", "vaga", "parking")):
            parking = int(_as_number(feature.get("value"))) or int(_as_number(feature.get("description")))
    if not parking:
        parking = int(_as_number(_property_value(properties, "garagem", "vagas", "parking", "carports"))) or _extrair_comodos(entity_text)[2]

    area = entity.get("floorSize") or entity.get("area") or entity.get("floorArea") or _property_value(properties, "area total", "area util", "area", "floor size") or _extrair_area(entity_text)
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

    numbers = {"um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "três": 3, "quatro": 4, "cinco": 5, "seis": 6}

    def extract_count(labels, choose_largest=False, prefer_value_before=False):
        label_pattern = "(?:" + "|".join(labels) + ")"
        value_pattern = r"(\d+|" + "|".join(numbers) + r")"
        if prefer_value_before:
            matches = list(re.finditer(rf"{value_pattern}\s*{label_pattern}", text, re.I))
            if matches:
                values = [match.group(1).lower() for match in matches]
                parsed = [int(value) if value.isdigit() else numbers[value] for value in values]
                return max(parsed, default=0) if choose_largest else parsed[0]
        matches = list(re.finditer(rf"{label_pattern}\s*[:\-]?\s*{value_pattern}", text, re.I))
        matches = [
            match for match in matches
            if not re.match(r"\s*(?:m²|m2|metros quadrados|área|area)", text[match.end():], re.I)
        ]
        if matches:
            values = [match.group(1).lower() for match in matches]
        else:
            matches = list(re.finditer(rf"{value_pattern}\s*{label_pattern}", text, re.I))
            values = [match.group(1).lower() for match in matches]
        if not matches:
            matches = list(re.finditer(rf"{label_pattern}\s+{value_pattern}", text, re.I))
            values = [match.group(1).lower() for match in matches]
        parsed = [int(value) if value.isdigit() else numbers[value] for value in values]
        return max(parsed, default=0) if choose_largest else (parsed[0] if parsed else 0)

    quartos = extract_count((r"quartos?", r"dormit[óo]rios?", r"dorms?", r"bedrooms?"))
    if not quartos:
        quartos = extract_count((r"suítes?", r"suites?"), choose_largest=True)
    banheiros = extract_count((r"banheiros?", r"bathrooms?"))
    garagem = extract_count((r"vagas?", r"garagens?", r"parking", r"carports?"), prefer_value_before=True)

    return quartos, banheiros, garagem


def _extrair_area(text: str) -> int:
    match = re.search(r"(\d{2,}(?:[.,]\d+)?)\s*(?:m²|m2|metros quadrados|m\s*quadrados)", text, re.I)
    if not match:
        match = re.search(r"(?:área total|área útil|area total|area util)\s*[:\-]?\s*(\d{2,}(?:[.,]\d+)?)", text, re.I)
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

        # Limite a coleta ao contêiner mais provável da galeria do anúncio.
        gallery_roots = _localizar_galerias(soup)
        for root in gallery_roots:
            for tag in root.find_all(["img", "source"]):
                for attr in ["src", "data-src", "data-lazy-src", "srcset"]:
                    value = tag.get(attr)
                    if not value:
                        continue
                    urls = [part.strip().split(" ")[0] for part in str(value).split(",")]
                    for image_url in urls:
                        if image_url.startswith("http") and not any(k in image_url.lower() for k in ["logo", "avatar", "icon", "badge"]):
                            imagens.append(image_url)

        # Só usa heurísticas genéricas quando nenhum contêiner nomeado foi encontrado.
        if not gallery_roots:
            imagens.extend(await _extrair_fotos_fallback(page, soup, url_imovel))

        for _ in range(12):
            try:
                for selector in _seletores_galeria():
                    cards = await page.query_selector_all(f"{selector} img, {selector} source")
                    for card in cards:
                        src = await card.get_attribute("src") or await card.get_attribute("data-src")
                        if src and src.startswith("http") and not any(k in src.lower() for k in ["logo", "avatar", "icon", "badge"]):
                            imagens.append(src)
                await page.mouse.wheel(0, 500)
                await asyncio.sleep(0.6)
            except Exception:
                break

        imagens_filtradas = []
        urls_vistas = set()
        urls_preferidas = {imagem.split("?")[0] for imagem in (preferred_urls or [])}
        termos_descartados = ("logo", "avatar", "icon", "badge", "banner", "favicon", "sprite", "tracking")
        termos_imovel = ("/properties/", "/property/", "/images/", "/uploads/", "/media/", "imovel", "foto", "photo", "gallery", "listing")
        for imagem in imagens:
            imagem = imagem.split("?")[0]
            imagem_lower = imagem.lower()
            if not imagem or imagem in urls_vistas or any(termo in imagem_lower for termo in termos_descartados):
                continue
            urls_vistas.add(imagem)
            prioridade = sum(1 for termo in termos_imovel if termo in imagem_lower)
            if imagem in urls_preferidas:
                prioridade += 100
            imagens_filtradas.append((prioridade, len(imagens_filtradas), imagem))

        # URLs do anúncio vêm antes de banners e imagens decorativas.
        imagens = [imagem for _, _, imagem in sorted(imagens_filtradas, key=lambda item: (-item[0], item[1]))]

        # O Render gratuito não possui disco persistente. Mantemos as URLs no
        # Neon e baixamos os arquivos somente durante a publicação.
        resultado = imagens[:12]
        if not gallery_roots and len(resultado) < 2:
            logger.warning(f"Fallback de galeria não encontrou fotos suficientes em {url_imovel}")
        return resultado

    except Exception as e:
        logger.warning(f"Erro fotos multi-site: {e}")
        return []


def _localizar_galerias(soup):
    """Retorna apenas raízes de galeria, evitando recomendações e imagens de layout."""
    gallery_terms = ("gallery", "galeria", "carousel", "carrossel", "swiper", "lightbox", "fotos", "photos", "property-images", "listing-media")
    excluded_terms = ("related", "similar", "semelhante", "recomend", "corretor", "agent", "suggest")
    candidates = []
    for tag in soup.find_all(["div", "section", "article", "ul"]):
        attrs = " ".join(str(tag.get(attr, "")) for attr in ("id", "class", "data-testid", "aria-label")).lower()
        if any(term in attrs for term in excluded_terms):
            continue
        images = tag.find_all(["img", "source"])
        named_score = sum(term in attrs for term in gallery_terms)
        score = named_score * 20 + min(len(images), 12)
        if named_score and images:
            candidates.append((score, len(images), tag))

    if candidates:
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected = []
        for _, _, tag in candidates:
            if any(tag is parent or tag in parent.parents for parent in selected):
                continue
            selected.append(tag)
            if len(selected) == 3:
                break
        return selected
    return []


def _tag_em_secao_excluida(tag):
    excluded_terms = ("related", "similar", "semelhante", "recomend", "corretor", "agent", "suggest", "partner", "parceir")
    current = tag
    while current and getattr(current, "name", None) != "html":
        attrs = " ".join(str(current.get(attr, "")) for attr in ("id", "class", "data-testid", "aria-label")).lower()
        if current.name in ("header", "footer", "nav", "aside") or any(term in attrs for term in excluded_terms):
            return True
        current = current.parent
    return False


def _urls_de_atributos_de_galeria(soup, url_imovel):
    urls = []
    attrs = ("data-src", "data-lazy-src", "data-fancybox", "data-lightbox", "data-gallery")
    for tag in soup.find_all(["img", "source", "a"]):
        if _tag_em_secao_excluida(tag):
            continue
        values = [tag.get(attr) for attr in attrs if tag.get(attr)]
        if tag.get("href") and any(tag.get(attr) for attr in ("data-fancybox", "data-lightbox", "data-gallery")):
            values.append(tag.get("href"))
        srcset = tag.get("srcset")
        if srcset and "," in srcset:
            values.extend(part.strip().split(" ")[0] for part in srcset.split(","))
        for value in values:
            if isinstance(value, str) and value.startswith(("http://", "https://", "/")):
                urls.append(urljoin(url_imovel, value))
    return list(dict.fromkeys(urls))


async def _extrair_fotos_fallback(page, soup, url_imovel):
    """Detecta galeria sem depender de classes semânticas do site."""
    attribute_urls = _urls_de_atributos_de_galeria(soup, url_imovel)
    if len(attribute_urls) >= 2:
        return attribute_urls

    try:
        visual_images = await page.locator("img").evaluate_all(
            """
            (images) => images.map((image) => {
                const rect = image.getBoundingClientRect();
                const excluded = /related|similar|semelhante|recomend|corretor|agent|suggest|partner|parceir/i;
                const excludedParent = [...image.closestAll ? image.closestAll('*') : []];
                let node = image;
                let inExcludedSection = false;
                while (node && node.tagName !== 'HTML') {
                    const marker = `${node.tagName} ${node.id || ''} ${node.className || ''} ${node.getAttribute('data-testid') || ''} ${node.getAttribute('aria-label') || ''}`;
                    if (/^(HEADER|FOOTER|NAV|ASIDE)$/.test(node.tagName) || excluded.test(marker)) {
                        inExcludedSection = true;
                        break;
                    }
                    node = node.parentElement;
                }
                const width = Number(image.getAttribute('width')) || image.naturalWidth || rect.width;
                const height = Number(image.getAttribute('height')) || image.naturalHeight || rect.height;
                return {
                    url: image.currentSrc || image.src || image.dataset.src || image.dataset.lazySrc,
                    width, height, inExcludedSection
                };
            })
            """
        )
    except Exception:
        visual_images = []

    valid_images = [
        image for image in visual_images
        if image.get("url") and image.get("width", 0) >= 150 and image.get("height", 0) >= 150 and not image.get("inExcludedSection")
    ]
    groups = {}
    for image in valid_images:
        ratio = round(image["width"] / image["height"], 1)
        size = (round(image["width"] / 100), round(image["height"] / 100))
        groups.setdefault((ratio, size), []).append(image)
    largest_group = max(groups.values(), key=len, default=[])
    visual_urls = [urljoin(url_imovel, image["url"]) for image in largest_group]
    return list(dict.fromkeys(attribute_urls + visual_urls))


def _seletores_galeria():
    return (
        "[class*='gallery']", "[class*='galeria']", "[class*='carousel']",
        "[class*='carrossel']", "[class*='swiper']", "[class*='lightbox']",
        "[data-testid*='gallery']", "[data-testid*='photo']",
    )
