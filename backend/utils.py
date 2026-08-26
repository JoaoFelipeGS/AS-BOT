import re
import time
import random
import logging
import os
import asyncio
from datetime import datetime
import requests
from fake_useragent import UserAgent
from backend.config import settings

def setup_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

logger = setup_logger("bot")
ua = UserAgent()

# ESTA É A FUNÇÃO QUE ESTÁ DANDO ERRO. ELA PRECISA ESTAR AQUI.
def baixar_imagem(url, destino):
    try:
        headers = {"User-Agent": ua.random}
        r = requests.get(url, timeout=20, headers=headers)
        if r.status_code != 200:
            return False
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        logger.error(f"Erro ao baixar imagem {url}: {e}")
        return False

def validar_imagem(caminho):
    try:
        return os.path.exists(caminho) and os.path.getsize(caminho) > 5000
    except:
        return False

def limpar(txt):
    if not txt: return ""
    return re.sub(r"\s+", " ", str(txt)).strip()

def limpar_preco(preco_str):
    if not preco_str: return 0.0
    try:
        preco = str(preco_str).replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(preco)
    except:
        return 0.0

async def scroll_humano(page):
    for _ in range(random.randint(2, 5)):
        try:
            await page.mouse.wheel(0, random.randint(300, 1200))
        except:
            pass
        await asyncio.sleep(random.uniform(0.5, 1.5))

async def delay_async(minimo=None, maximo=None):
    minimo = minimo or settings.delay_min
    maximo = maximo or settings.delay_max
    await asyncio.sleep(random.uniform(minimo, maximo))
