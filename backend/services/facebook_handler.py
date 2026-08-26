import re
import asyncio
import json
import os
import random
from playwright.async_api import Page
from backend.config import settings
from backend.utils import setup_logger

logger = setup_logger("facebook_handler")
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
        # Se o texto for longo, não usamos .type() com delay para evitar cortes e lentidão
        if len(texto_final) > 150:
            await locator.click(force=True)
            await asyncio.sleep(0.5)
            
            # Limpa o campo
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            
            # Injeta o valor via JavaScript instantaneamente
            await locator.evaluate(f"""
                el => {{
                    const proto = el.tagName === 'TEXTAREA' 
                        ? window.HTMLTextAreaElement.prototype 
                        : window.HTMLInputElement.prototype;
                    const setter = Object.getOwnPropertyDescriptor(proto, 'value');
                    if (setter && setter.set) {{
                        setter.set.call(el, `{texto_final.replace('`', '\\`').replace('$', '\\$')}`);
                    }}
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                }}
            """)
            logger.info("Texto longo injetado via JS com sucesso.")
            await asyncio.sleep(0.5)
            await page.keyboard.press("Tab")
            return True

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

async def _upload_imagens_por_referencia(page, url_imovel, imovel_id):
    try:
        if not url_imovel: return False
        referencia = url_imovel.split("/")[-1].split("?")[0]
        pasta_fotos = os.path.join(settings.dir_images, referencia)
        if not os.path.exists(pasta_fotos): return False

        arquivos = [os.path.abspath(os.path.join(pasta_fotos, f)) for f in os.listdir(pasta_fotos) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
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
            logger.info(f"--- INICIANDO SEQUÊNCIA: Imóvel {imovel_id} ---")
            await page.goto(FACEBOOK_RENTAL_URL, wait_until="domcontentloaded")
            await asyncio.sleep(7)

            # 1. FOTOS
            url_imovel = dados_imovel.get('url', '')
            if await _upload_imagens_por_referencia(page, url_imovel, imovel_id):
                logger.info(f"[{imovel_id}] ✅ Fotos enviadas.")
                await asyncio.sleep(10) 
            else:
                logger.warning(f"[{imovel_id}] ⚠️ Fotos falharam.")

            # 2. PREÇO
            preco_input = await _achar_input_original(page, ["Preço", "Price"])
            if preco_input:
                await _type_original_fixed(page, preco_input, str(dados_imovel.get('preco', '0')), is_price=True)

            # 3. QUARTOS
            quartos_input = await _achar_input_original(page, ["Número de quartos", "Bedrooms"])
            if quartos_input:
                await _type_original_fixed(page, quartos_input, str(dados_imovel.get('quartos', '1')))

            # 4. BANHEIROS
            banheiros_input = await _achar_input_original(page, ["Número de banheiros", "Bathrooms"])
            if banheiros_input:
                await _type_original_fixed(page, banheiros_input, str(dados_imovel.get('banheiros', '1')))

            # 5. DESCRIÇÃO COM ASSINATURA (AGORA ULTRA ROBUSTO)
            try:
                descricao_base = str(dados_imovel.get('descricao', ''))
                assinatura = "\n\nAS Imobiliária\nCRECI 28.188-J"
                descricao_final = f"{descricao_base}{assinatura}"
                
                logger.info(f"[{imovel_id}] Preenchendo descrição completa (Tamanho: {len(descricao_final)} caracteres)...")
                
                # Tenta localizar a textarea
                textarea = page.locator("textarea").last
                await textarea.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                
                # Usa a função de digitação que agora diferencia texto curto de longo
                success = await _type_original_fixed(page, textarea, descricao_final)
                
                if not success:
                    logger.error(f"[{imovel_id}] Falha ao preencher a descrição.")
                else:
                    logger.info(f"[{imovel_id}] Descrição e assinatura preenchidas com sucesso.")

            except Exception as e:
                logger.warning(f"[{imovel_id}] Erro ao preencher descrição: {e}")

            # F12 para forçar o botão Avançar
            await _simular_f12_console(page)

            logger.info(f"✅ Imóvel {imovel_id} preenchido com sucesso. Aguardando confirmação manual.")
            return True

        except Exception as e:
            logger.error(f"❌ Erro fatal no imóvel {imovel_id}: {e}")
            return False
