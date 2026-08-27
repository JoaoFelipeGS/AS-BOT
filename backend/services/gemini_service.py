import asyncio
import os
import re
import requests
from backend.logging import logger

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"


class GeminiService:

    # =========================
    # REQUEST
    # =========================
    def _post_request(self, prompt: str, timeout: int = 60):
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            logger.warning("Groq não configurado: GROQ_API_KEY ausente")
            return None
        model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Você é um redator especializado em anúncios de imóveis para o Facebook Marketplace. "
                        "Você reescreve descrições de imóveis no formato de anúncio, mantendo TODAS as "
                        "informações originais (preço, endereço, metragem, número de quartos, banheiros, "
                        "vagas de garagem, diferenciais, etc). Você NUNCA inventa dados que não estão no "
                        "texto original. Você responde APENAS com o anúncio finalizado, sem comentários, "
                        "sem introduções como 'Aqui está' e sem explicações sobre o que você fez."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4
        }

        try:
            r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=timeout)

            if r.status_code != 200:
                logger.error(f"Groq error HTTP {r.status_code} para o modelo configurado")
                return None

            return r.json()["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"Request error: {e}")
            return None

    # =========================
    # LIMPEZA DE TEXTO
    # =========================
    def _clean_text(self, text: str) -> str:
        if not text:
            return text

        # remove markdown de ênfase, mantém o resto intacto
        text = text.replace("**", "").replace("*", "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # remove possíveis preâmbulos do tipo "Aqui está o anúncio:" antes do conteúdo real
        text = re.sub(
            r"^\s*(aqui est[áa].*?:|segue.*?:|anúncio.*?:)\s*\n+",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # normaliza linhas (tira espaços nas pontas de cada linha)
        lines = [line.strip() for line in text.split("\n")]

        # remove linhas vazias duplicadas seguidas
        cleaned = []
        last_empty = False
        for line in lines:
            if line == "":
                if not last_empty:
                    cleaned.append("")
                last_empty = True
            else:
                cleaned.append(line)
                last_empty = False

        text = "\n".join(cleaned)

        # remove excesso de quebras de linha (3+ -> 2)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    # =========================
    # VALIDAÇÃO
    # =========================
    def _is_valid(self, text: str) -> bool:
        if not text:
            return False

        # tamanho mínimo razoável para um anúncio
        if len(text.strip()) < 60:
            return False

        # rejeita respostas que são claramente meta-comentário da IA
        # (ex: "Não posso ajudar", "Como assistente de IA...")
        lowered = text.lower()
        red_flags = [
            "não posso ajudar",
            "como modelo de linguagem",
            "como assistente de ia",
            "i cannot",
            "i can't help",
        ]
        if any(flag in lowered for flag in red_flags):
            return False

        return True

    # =========================
    # PROMPT — FORMATO DE ANÚNCIO FACEBOOK
    # =========================
    def _build_prompt(self, text: str) -> str:
        return f"""Reescreva a descrição de imóvel abaixo no formato de ANÚNCIO PARA O FACEBOOK MARKETPLACE.

FORMATO OBRIGATÓRIO DA SAÍDA (siga exatamente esta estrutura, com as mesmas quebras de linha):
🏠 [Tipo de imóvel, ex: Casa/Apartamento/Sobrado] à venda em [Cidade]
📌 Bairro [Nome do bairro]

✅ Descrição do imóvel
[Texto corrido, em um ou poucos parágrafos, narrando os ambientes e diferenciais do imóvel exatamente como estão no texto original — quartos, banheiros, garagem, área, áreas de lazer, acabamentos, etc. Não transforme em lista nem use emojis dentro desse parágrafo. Apenas reescreva de forma fluida e natural, como uma descrição de anúncio.]

📲 Chame agora mesmo e agende sua visita!

REGRAS IMPORTANTES:
- NÃO inclua o preço/valor do imóvel no anúncio, em nenhuma hipótese
- NÃO inclua dados de corretor, CRECI ou telefone
- Se a cidade não estiver explícita no texto original, omita "em [Cidade]" na primeira linha
- Se o bairro não estiver no texto original, omita a linha "📌 Bairro..."
- Não invente nenhuma informação que não esteja no texto original
- Não remova nenhum dado relevante do texto original (exceto o preço, que deve ser omitido)
- A descrição deve ficar em texto corrido, não em lista de características com emojis
- Mantenha linguagem persuasiva, mas profissional, sem exagero
- Responda APENAS com o anúncio final, sem comentários antes ou depois

TEXTO ORIGINAL:
{text}

ANÚNCIO FINAL:
"""

    # =========================
    # MAIN
    # =========================
    async def reformulate_description(self, text: str, timeout: int = 60):
        if not text or len(text.strip()) < 10:
            return text

        prompt = self._build_prompt(text)

        for attempt in range(2):
            result = await asyncio.to_thread(
                self._post_request,
                prompt,
                timeout
            )

            if not result:
                logger.warning(f"Tentativa {attempt + 1}: sem resposta da API")
                continue

            cleaned = self._clean_text(result)

            if self._is_valid(cleaned):
                return cleaned

            logger.warning(f"Tentativa {attempt + 1} falhou na validação. Resposta recebida: {cleaned[:200]!r}")

        # fallback seguro: mantém o texto original (apenas limpo)
        logger.info("⚠️ Descrição mantida (IA retornou original ou falhou)")
        return self._clean_text(text)


gemini_service = GeminiService()