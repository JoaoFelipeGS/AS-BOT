import os
import re
import asyncio
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

    titulo = _extrair_titulo(soup, text)
    descricao = _extrair_descricao(soup, text)
    preco = _extrair_preco(text)
    quartos, banheiros, garagem = _extrair_comodos(text)
    area = _extrair_area(text)
    endereco = _extrair_endereco(soup, text)
    fotos = await _extrair_fotos(page, soup, url)

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
    match = re.search(r"(\d{2,})\s*(?:m²|m2|metros quadrados|m\s*quadrados|área)", text, re.I)
    if match:
        return int(match.group(1))
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


async def _extrair_fotos(page, soup, url_imovel):
    imagens = []
    try:
        for tag in soup.find_all(["img", "source"]):
            for attr in ["src", "data-src", "data-lazy-src", "srcset"]:
                value = tag.get(attr)
                if not value:
                    continue
                urls = [part.strip().split(" ")[0] for part in str(value).split(",")]
                for url in urls:
                    if not url.startswith("http"):
                        continue
                    if any(k in url.lower() for k in ["logo", "avatar", "icon", "badge"]):
                        continue
                    if url not in imagens:
                        imagens.append(url)

        for _ in range(12):
            try:
                cards = await page.query_selector_all("img")
                for card in cards:
                    src = await card.get_attribute("src") or await card.get_attribute("data-src")
                    if src and src.startswith("http") and "logo" not in src.lower() and src not in imagens:
                        imagens.append(src)
                await page.mouse.wheel(0, 500)
                await asyncio.sleep(0.6)
            except Exception:
                break

        imagens = [img.split("?")[0] for img in imagens if img]
        imagens = list(dict.fromkeys(imagens))

        referencia = url_imovel.split("/")[-1].split("?")[0]
        pasta_imovel = os.path.join(settings.dir_images, referencia)
        os.makedirs(pasta_imovel, exist_ok=True)

        arquivos_salvos = []
        for idx, img_url in enumerate(imagens[:12]):
            try:
                ext = ".jpg"
                if img_url.lower().endswith(".png"):
                    ext = ".png"
                elif img_url.lower().endswith(".webp"):
                    ext = ".webp"
                destino = os.path.join(pasta_imovel, f"{idx + 1}{ext}")
                if utils.baixar_imagem(img_url, destino) and utils.validar_imagem(destino):
                    arquivos_salvos.append(os.path.abspath(destino))
            except Exception:
                continue

        return arquivos_salvos

    except Exception as e:
        logger.warning(f"Erro fotos multi-site: {e}")
        return []
