from backend.logging import logger
from backend.config import settings
from backend.services import facebook_handler as legacy_facebook
from backend.database import SessionLocal
from backend.models import Fila, Imovel
from backend.browser_manager import browser_manager

class PublisherService:

    @staticmethod
    async def publish(fila_id: int) -> bool:
        # 1. FASE DE COLETA DE DADOS
        # Abrimos a sessão, pegamos o que precisamos e FECHAMOS IMEDIATAMENTE
        try:
            with SessionLocal() as db:
                fila = db.query(Fila).filter(Fila.id == fila_id).first()
                if not fila: 
                    logger.error(f"Item de fila {fila_id} não encontrado.")
                    return False

                imovel = db.query(Imovel).filter(Imovel.id == fila.imovel_id).first()
                if not imovel: 
                    logger.error(f"Imóvel {fila.imovel_id} não encontrado.")
                    return False

                # Extraímos os dados para variáveis simples (não dependem do banco)
                dados_imovel = {
                    "preco": imovel.preco,
                    "descricao": imovel.descricao,
                    "quartos": imovel.quartos,
                    "banheiros": imovel.banheiros,
                    "garagem": imovel.garagem,
                    "imagens_json": imovel.imagens_json,
                    "url": imovel.url
                }
                imovel_id = fila.imovel_id
        except Exception as e:
            logger.error(f"Erro ao coletar dados do banco: {e}")
            return False

        # 2. FASE DE AUTOMAÇÃO (O BOT TRABALHANDO)
        # Aqui o banco de dados está FECHADO. O bot pode demorar 10 minutos e não haverá erro de SSL ou Lock.
        try:
            session = await browser_manager.get_session("admin")
            if not session:
                session = await browser_manager.create_session("admin")

            page = await session.new_page()

            # Chamada ao handler do facebook (aquela que demora)
            result = await legacy_facebook.publicar_imovel(
                page=page,
                imovel_id=imovel_id,
                fila_id=fila_id,
                dados_imovel=dados_imovel
            )

            # 3. FASE DE ATUALIZAÇÃO DE STATUS
            # Agora que o bot terminou, abrimos uma NOVA conexão rápida apenas para atualizar o status
            if result:
                with SessionLocal() as db_update:
                    fila_item = db_update.query(Fila).filter(Fila.id == fila_id).first()
                    if fila_item:
                        fila_item.status = "aguardando_confirmacao"
                        db_update.commit()
                        logger.info(f"✅ Status do imóvel {imovel_id} atualizado para 'aguardando_confirmacao'")

                print("\n" + "="*60)
                print("🤖 BOT: SESSÃO ATIVA E CAMPOS PREENCHIDOS!")
                print("👉 O botão 'Avançar' deve estar visível. Publique e confirme no site.")
                print("="*60 + "\n")

            return result

        except Exception as e:
            logger.error(f"Erro durante a execução do bot: {e}")
            return False

publisher_service = PublisherService()
