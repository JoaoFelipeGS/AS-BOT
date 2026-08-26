from datetime import datetime, timedelta
import config
import utils
import database

logger = utils.setup_logger("error_handler")


# =========================================================
# DETECÇÃO DE BLOQUEIO
# =========================================================

async def verificar_bloqueio(page):

    try:
        url = (page.url or "").lower()

        try:
            html = (await page.content()).lower()
        except:
            html = ""

        # =====================================================
        # CHECKPOINT REAL (precisa evidência)
        # =====================================================

        if "checkpoint" in url:
            if any(x in html for x in ["security", "code", "confirm", "verify"]):
                return {"bloqueado": True, "tipo": "checkpoint"}

        # =====================================================
        # LOGOUT REAL
        # =====================================================

        if "login" in url and "marketplace" not in url:
            return {"bloqueado": True, "tipo": "logout"}

        # =====================================================
        # CAPTCHA REAL (contextual)
        # =====================================================

        if ("captcha" in html or "recaptcha" in html):
            if "marketplace" not in url:
                return {"bloqueado": True, "tipo": "captcha"}

        # =====================================================
        # RATE LIMIT REAL
        # =====================================================

        rate_keywords = [
            "try again later",
            "rate limit",
            "too many requests",
            "temporarily unavailable"
        ]

        if any(x in html for x in rate_keywords):
            return {"bloqueado": True, "tipo": "rate_limit"}

    except Exception as e:
        logger.error(f"erro verificação bloqueio: {e}")

    return {"bloqueado": False, "tipo": None}


# =========================================================
# TRATAMENTO
# =========================================================

def tratar_bloqueio(page, tipo):

    logger.warning(f"BLOQUEIO DETECTADO: {tipo}")

    database.db.registrar_bloqueio(
        tipo,
        datetime.now().isoformat()
    )

    mensagens = {
        "checkpoint": "⚠️ Checkpoint detectado. Resolva manualmente.",
        "logout": "🔐 Faça login novamente.",
        "captcha": "🤖 Resolva o captcha.",
        "rate_limit": "⏸️ Aguarde algumas horas."
    }

    print("\n" + mensagens.get(tipo, "Bloqueio detectado"))
    input("\nENTER para continuar...")


# =========================================================
# BLOQUEIO ATIVO (CORRIGIDO DE VERDADE)
# =========================================================

def verificar_bloqueio_ativo():

    bloqueio = database.db.obter_bloqueio_ativo()

    if not bloqueio:
        return False

    try:
        tipo = bloqueio[1]
        criado = bloqueio[2] if len(bloqueio) > 2 else None

        # ignora bloqueios inválidos
        if not tipo or tipo == "unknown":
            return False

        if not criado:
            return False

        # converte string para datetime
        if isinstance(criado, str):
            try:
                criado = datetime.fromisoformat(criado)
            except:
                return False

        # expiração real (2h)
        if datetime.now() - criado > timedelta(hours=2):
            logger.warning("Bloqueio expirado automaticamente")
            return False

        return True

    except Exception as e:
        logger.error(f"erro bloqueio ativo: {e}")
        return False


# =========================================================
# VALIDAÇÃO PRÉ-PUBLICAÇÃO
# =========================================================

def validar_antes_publicar():

    if verificar_bloqueio_ativo():
        return False, "Bloqueio temporário ativo"

    return True, "OK"