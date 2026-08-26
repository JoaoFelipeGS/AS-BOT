import asyncio
import traceback
import json

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session
from playwright.async_api import TimeoutError, async_playwright

# --- IMPORTS CORRIGIDOS PARA MODO ABSOLUTO ---
from backend.services import extractor as legacy_extractor
import backend.utils as legacy_utils
from backend.config import settings
from backend.logging import logger
from backend.models import Imovel
from backend.services.gemini_service import gemini_service
from backend.stealth import stealth
# --------------------------------------------

class ExtractorService:

    @staticmethod
    def save_imovel(data: dict, db: Session) -> Imovel:

        if not data:
            return None

        existing = (
            db.query(Imovel)
            .filter(Imovel.url == data.get("url"))
            .first()
        )

        if not existing:
            existing = Imovel(
                url=data.get("url")
            )
            db.add(existing)

        def clean_text(v, max_len):
            return (v or "").strip()[:max_len]

        existing.titulo = clean_text(
            data.get("titulo"),
            300
        )

        existing.preco = legacy_utils.limpar_preco(
            data.get("preco", 0)
        )

        existing.descricao = clean_text(
            data.get("descricao"),
            8000
        )

        existing.endereco = clean_text(
            data.get("endereco"),
            500
        )

        existing.quartos = int(
            data.get("quartos") or 0
        )

        existing.banheiros = int(
            data.get("banheiros") or 0
        )

        existing.garagem = int(
            data.get("garagem") or 0
        )

        existing.area = int(
            data.get("area") or 0
        )

        fotos = data.get("fotos") or []

        if not isinstance(fotos, list):
            fotos = []

        existing.imagens_json = json.dumps(
            fotos
        )

        existing.atualizado_em = datetime.utcnow()

        db.commit()

        db.refresh(existing)

        return existing

    # =====================================================
    # EXTRACT
    # =====================================================

    @staticmethod
    async def extract_and_save(
        url: str,
        db: Session
    ) -> Optional[Imovel]:

        logger.info(
            f"Iniciando extração: {url}"
        )

        browser = None

        try:

            profile_path = Path(
                settings.persistent_profile
            )

            profile_path.mkdir(
                parents=True,
                exist_ok=True
            )

            async with async_playwright() as p:

                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ],
                )

                context = await browser.new_context(
                    viewport={
                        "width": 1400,
                        "height": 900
                    },
                    locale="pt-BR",
                    ignore_https_errors=True,
                    extra_http_headers={
                        "Accept-Language": "pt-BR,pt;q=0.9"
                    },
                )

                page = await context.new_page()

                try:

                    await page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=120000
                    )

                except TimeoutError:

                    logger.warning(
                        f"Timeout inicial: {url}"
                    )

                except Exception as e:

                    logger.warning(
                        f"Erro navegação: {e}"
                    )

                if await _is_antibot_checkpoint(page):
                    raise RuntimeError(
                        "O site bloqueou a automação com um checkpoint anti-bot. "
                        "A imobiliária precisa autorizar o acesso do bot ou fornecer uma rota de acesso autorizada."
                    )

                await legacy_utils.delay_async()
                await stealth(page)

                try:
                    await legacy_utils.scroll_humano(page)
                except:
                    pass

                # 1. EXTRAÇÃO BASE (A única fonte de dados reais)
                data = await legacy_extractor.extrair_dados(
                    page,
                    url
                )

                if not data:

                    logger.warning(
                        f"Falha extração: {url}"
                    )

                    return None

                # 2. LIMPEZA BÁSICA DE TEXTO
                lixo_keywords = [

                    "copiado",
                    "+55",
                    "telefone",
                    "email",
                    "formulário",
                    "nome",
                    "brazil"
                ]

                if data.get("descricao"):

                    desc = data["descricao"]

                    for l in lixo_keywords:
                        desc = desc.replace(l, "")

                    data["descricao"] = desc.strip()

                # ==========================================================================
                # 🚀 REFORMULAÇÃO DA DESCRIÇÃO COM IA (APENAS DESCRIÇÃO)
                # ==========================================================================
                if data.get("descricao"):
                    try:
                        logger.info(f"Reformulando descrição para: {url}")
                        # Chamamos apenas a função de copywriting
                        reformulated = await gemini_service.reformulate_description(
                            data["descricao"]
                        )
                        if reformulated and reformulated != data["descricao"]:
                            data["descricao"] = reformulated
                            logger.info("✅ Descrição reformulada com sucesso!")
                        else:
                            logger.info("⚠️ Descrição mantida (IA retornou original ou falhou)")
                    except Exception as e:
                        logger.warning(f"Erro ao chamar reformulação: {e}")
                # ==========================================================================

                # 3. SALVAMENTO (Preço, quartos, etc, vêm apenas do extrator base)
                imovel = (
                    ExtractorService
                    .save_imovel(data, db)
                )

                if not imovel:

                    logger.error(
                        "Falha salvar imóvel"
                    )

                    return None

                logger.info(
                    f"Imóvel salvo: {imovel.id}"
                )

                await context.close()

                await browser.close()

                return imovel

        except Exception as e:

            logger.error(
                f"Erro extração {url}: {e}"
            )

            logger.error(
                traceback.format_exc()
            )

            try:

                if browser:
                    await browser.close()

            except:
                pass

            return None


extractor_service = ExtractorService()


async def _is_antibot_checkpoint(page) -> bool:
    try:
        title = (await page.title()).lower()
        body_text = (await page.locator("body").inner_text(timeout=5000)).lower()
        markers = (
            "vercel security checkpoint",
            "ponto de verificação de segurança da vercel",
            "enable javascript to continue",
            "checking your browser",
        )
        return any(marker in title or marker in body_text for marker in markers)
    except Exception:
        return False

