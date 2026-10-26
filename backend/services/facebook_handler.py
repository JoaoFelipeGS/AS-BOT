import re
import asyncio
import json
import os
import random
import tempfile
from urllib.parse import urlparse
from playwright.async_api import Page
import backend.utils as utils

logger = utils.setup_logger("facebook_handler")
FACEBOOK_RENTAL_URL = "https://www.facebook.com/marketplace/create/rental"

# =========================================================
# 🔒 TRAVA DE SEGURANÇA (SEQUENCIADOR)
# =========================================================
publish_lock = asyncio.Lock()

# =========================================================
# 1. SIMULAÇÃO DE ABRIR/FECHAR CONSOLE
# =========================================================
async def _simular_f12_console(page: Page):
    try:
        logger.info("Simulando abertura e fechamento do console (F12)...")
        await page.keyboard.press("F12")
        await asyncio.sleep(1)
        await page.keyboard.press("F12")
        await asyncio.sleep(1)
        await page.evaluate("window.dispatchEvent(new Event('resize'));")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        logger.info("Simulação de console concluída.")
    except Exception as e:
        logger.warning(f"Erro ao simular F12: {e}")

# =========================================================
# 2. LÓGICA de DIGITAÇÃO MELHORADA
# =========================================================
async def _type_original_fixed(page: Page, locator, value: str, is_price=False):
    try:
        if is_price:
            try:
                texto_final = str(int(float(str(value).replace(',', '.'))))
            except:
                texto_final = re.sub(r'[^\d]', '', str(value))
        else:
            texto_final = str(value)

        # --- MÉTODO PARA TEXTOS LONGOS (DESCRIÇÃO) ---
        if len(texto_final) > 150:
            return await _preencher_descricao(page, locator, texto_final)

        # --- MÉTODO PARA TEXTOS CURTOS (Preço, Quartos, etc) ---
        await locator.click(force=True)
        await asyncio.sleep(0.5)

        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await locator.fill("") 
        
        await locator.type(texto_final, delay=random.randint(60, 120))
        await asyncio.sleep(0.5)

        await locator.evaluate("""
            el => {
                const proto = el.tagName === 'TEXTAREA'
                    ? window.HTMLTextAreaElement.prototype
                    : window.HTMLInputElement.prototype;
                const setter = Object.getOwnPropertyDescriptor(proto, 'value');
                if (setter && setter.set) {
                    setter.set.call(el, el.value);
                }
                el.dispatchEvent(new Event('input',  { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur',   { bubbles: true }));
            }
        """)
        
        await asyncio.sleep(0.3)
        await page.keyboard.press("Tab")
        return True
    except Exception as e:
        logger.warning(f"Erro na digitação: {e}")
        return False


async def _preencher_descricao(page: Page, locator, value: str) -> bool:
    try:
        await locator.fill(value, timeout=10000)
        actual = await locator.evaluate(
            "el => el.isContentEditable ? el.innerText : el.value"
        )
        if (actual or "").strip() != value.strip():
            logger.error("O campo de texto não manteve a descrição completa.")
            return False
        await page.keyboard.press("Tab")
        logger.info("Descrição preenchida e validada.")
        return True
    except Exception as error:
        logger.warning("Falha ao preencher a descrição (%s)", error.__class__.__name__)
        return False


# =========================================================
# 3. BUSCA E UPLOAD
# =========================================================
async def _achar_input_original(page, termos):
    for termo in termos:
        try:
            resultado = await page.evaluate(f"""
                () => {{
                    const termo = "{termo}".toLowerCase();
                    const todos = document.querySelectorAll('label, span, div');
                    for (const el of todos) {{
                        const txt = el.textContent.trim().toLowerCase();
                        if (txt !== termo) continue;
                        let parent = el.parentElement;
                        while (parent && parent !== document.body) {{
                            const inputs = parent.querySelectorAll('input[type="text"], input[type="number"]');
                            if (inputs.length === 1 && inputs[0].offsetParent !== null) {{
                                return inputs[0].id || 'found_by_index'; 
                            }}
                            parent = parent.parentElement;
                        }}
                    }}
                    return null;
                }}
            """)
            if resultado:
                return page.locator(f"#{resultado}" if resultado != 'found_by_index' else "input").first
        except: continue
    return None


async def _achar_campo_descricao(page):
    selectors = (
        '[aria-label="Descrição"]',
        '[aria-label="Description"]',
        '[placeholder="Descrição"]',
        '[placeholder="Description"]',
        "textarea",
        '[contenteditable="true"][role="textbox"]',
        '[contenteditable="true"]',
    )
    for selector in selectors:
        candidates = page.locator(selector)
        for index in range(await candidates.count()):
            candidate = candidates.nth(index)
            if await candidate.is_visible():
                return candidate
    raise RuntimeError("Campo de descrição visível não encontrado no formulário")


async def _upload_imagens_por_referencia(page, image_urls, imovel_id):
    try:
        if isinstance(image_urls, str):
            try:
                image_urls = json.loads(image_urls)
            except json.JSONDecodeError:
                image_urls = []
        if not image_urls: return False

        with tempfile.TemporaryDirectory(prefix=f"onora-imob-{imovel_id}-") as temp_dir:
            arquivos = []
            for index, image_url in enumerate(image_urls[:12]):
                if not isinstance(image_url, str) or not image_url.startswith(('http://', 'https://')):
                    continue
                suffix = os.path.splitext(urlparse(image_url).path)[1].lower()
                if suffix not in ('.jpg', '.jpeg', '.png', '.webp'):
                    suffix = '.jpg'
                destino = os.path.join(temp_dir, f"{index + 1}{suffix}")
                if utils.baixar_imagem(image_url, destino) and utils.validar_imagem(destino):
                    arquivos.append(destino)
            if not arquivos: return False

            input_file = page.locator("input[type='file']").first
            await input_file.wait_for(state="attached", timeout=20000)
            await input_file.evaluate("el => { el.style.display = 'block'; el.style.visibility = 'visible'; }")
            await input_file.set_input_files(arquivos)
            return True
    except Exception as e:
        logger.error(f"Erro upload: {e}")
        return False

# =========================================================
# 4. FLUXO DE PUBLICAÇÃO FINAL (Sincronizado)
# =========================================================
async def publicar_imovel(page: Page, imovel_id: int, fila_id: int, dados_imovel: dict):
    async with publish_lock:
        try:
            logger.info(f"--- INICIANDO SEQUÊNCIA: Imóvel {imovel_id}, fila {fila_id} ---")
            await page.goto(FACEBOOK_RENTAL_URL, wait_until="domcontentloaded")
            await asyncio.sleep(7)

            # 1. FOTOS
            if await _upload_imagens_por_referencia(page, dados_imovel.get('imagens_json', []), imovel_id):
                logger.info(f"[{imovel_id}] ✅ Fotos enviadas.")
                await asyncio.sleep(10) 
            else:
                logger.error(f"[{imovel_id}] Falha no upload das fotos; publicação interrompida.")
                return False

            # 2. PREÇO
            preco_input = await _achar_input_original(page, ["Preço", "Price"])
            if not preco_input or not await _type_original_fixed(
                page, preco_input, str(dados_imovel.get('preco', '0')), is_price=True
            ):
                logger.error(f"[{imovel_id}] Campo de preço ausente ou não preenchido.")
                return False

            # 3. QUARTOS
            quartos_input = await _achar_input_original(page, ["Número de quartos", "Bedrooms"])
            if not quartos_input or not await _type_original_fixed(
                page, quartos_input, str(dados_imovel.get('quartos', '1'))
            ):
                logger.error(f"[{imovel_id}] Campo de quartos ausente ou não preenchido.")
                return False

            # 4. BANHEIROS
            banheiros_input = await _achar_input_original(page, ["Número de banheiros", "Bathrooms"])
            if not banheiros_input or not await _type_original_fixed(
                page, banheiros_input, str(dados_imovel.get('banheiros', '1'))
            ):
                logger.error(f"[{imovel_id}] Campo de banheiros ausente ou não preenchido.")
                return False

            # 5. DESCRIÇÃO COM ASSINATURA (AGORA ULTRA ROBUSTO)
            descricao_base = str(dados_imovel.get('descricao', '')).strip()
            if not descricao_base:
                logger.error(f"[{imovel_id}] Descrição vazia; publicação interrompida.")
                return False
            assinatura = "\n\nAS Imobiliária\nCRECI 28.188-J"
            descricao_final = f"{descricao_base}{assinatura}"

            logger.info(f"[{imovel_id}] Preenchendo descrição completa (Tamanho: {len(descricao_final)} caracteres)...")
            try:
                description_field = await _achar_campo_descricao(page)
                await description_field.scroll_into_view_if_needed()
                success = await _preencher_descricao(page, description_field, descricao_final)
            except Exception as error:
                logger.error(
                    f"[{imovel_id}] Campo de descrição indisponível; publicação interrompida "
                    f"({error.__class__.__name__})."
                )
                return False

            if not success:
                logger.error(f"[{imovel_id}] Falha ao preencher a descrição; publicação interrompida.")
                return False

            # F12 para forçar o botão Avançar
            await _simular_f12_console(page)

            logger.info(f"✅ Imóvel {imovel_id} preenchido com sucesso. Aguardando confirmação manual.")
            return True

        except Exception as e:
            logger.error(f"❌ Erro fatal no imóvel {imovel_id}: {e}")
            return False
