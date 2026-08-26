import os
import base64
import asyncio
import pytesseract
from PIL import Image
from playwright.async_api import Page
import aiohttp


class UIVisionAgent:

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

    # =====================================================
    # SCREENSHOT
    # =====================================================
    async def screenshot(self, page: Page) -> str:
        path = "ui_state.png"
        await page.screenshot(path=path, full_page=True)
        return path

    # =====================================================
    # OCR LOCAL (fallback)
    # =====================================================
    def ocr(self, image_path: str) -> str:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img)

    # =====================================================
    # GEMINI VISION CLASSIFIER
    # =====================================================
    async def classify_fields(self, image_path: str, ocr_text: str):

        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        prompt = f"""
Você é um agente de UI.

A imagem mostra um formulário do Facebook Marketplace.

OCR detectado:
{ocr_text}

Identifique APENAS:
- campo título
- campo preço
- campo descrição
- input de upload de imagens

Responda JSON:
{{
  "title": "selector_hint",
  "price": "selector_hint",
  "description": "selector_hint",
  "upload": "selector_hint"
}}
"""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}",
                json={
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {
                                "mime_type": "image/png",
                                "data": img_b64
                            }}
                        ]
                    }]
                }
            ) as resp:
                data = await resp.json()

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return eval(text) if isinstance(text, str) else text
        except:
            return None


ui_agent = UIVisionAgent()