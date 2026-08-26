from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from backend.models import Fila, Imovel
from ..logging import logger

class QueueService:

    @staticmethod
    def dashboard_stats(db: Session):
        try:
            total_extraidos = db.query(Imovel).count()
            total_publicados = db.query(Fila).filter(Fila.status == "publicado").count()
            total_erros = db.query(Fila).filter(Fila.status == "erro").count()
            total_bloqueios = db.query(Fila).filter(Fila.status == "bloqueado").count()
            fila_pendente = db.query(Fila).filter(Fila.status == "aguardando").count()
            total_processados = total_publicados + total_erros
            taxa_sucesso = round((total_publicados / total_processados) * 100, 2) if total_processados > 0 else 0.0
            return {
                "total_extraidos": total_extraidos,
                "total_publicados": total_publicados,
                "total_erros": total_erros,
                "total_bloqueios": total_bloqueios,
                "fila_pendente": fila_pendente,
                "taxa_sucesso": taxa_sucesso,
            }
        except Exception as e:
            logger.exception(f"Erro ao gerar dashboard: {e}")
            return {"total_extraidos": 0, "total_publicados": 0, "total_erros": 0, "total_bloqueios": 0, "fila_pendente": 0, "taxa_sucesso": 0.0}

    @staticmethod
    def list_queue(db: Session, limit: int = 50):
        try:
            return db.query(Fila).options(joinedload(Fila.imovel)).order_by(Fila.agendado_para.asc()).limit(limit).all()
        except Exception as e:
            logger.exception(f"Erro ao listar fila: {e}")
            return []

    @staticmethod
    def get_item(db: Session, fila_id: int):
        try:
            return db.query(Fila).options(joinedload(Fila.imovel)).filter(Fila.id == fila_id).first()
        except Exception as e:
            logger.exception(f"Erro ao buscar item da fila: {e}")
            return None

    @staticmethod
    def add_to_queue(db: Session, imovel_id: int):
        try:
            imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
            if not imovel: return None
            fila_existente = db.query(Fila).filter(Fila.imovel_id == imovel_id, Fila.status.in_(["aguardando", "processando"])).first()
            if fila_existente: return fila_existente
            fila = Fila(imovel_id=imovel_id, status="aguardando", tentativas=0, agendado_para=datetime.utcnow(), criado_em=datetime.utcnow(), atualizado_em=datetime.utcnow())
            db.add(fila)
            db.commit()
            db.refresh(fila)
            return fila
        except Exception as e:
            db.rollback()
            logger.exception(f"Erro ao adicionar à fila: {e}")
            return None

    @staticmethod
    def delete_queue(db: Session, fila_id: int):
        try:
            fila = db.query(Fila).filter(Fila.id == fila_id).first()
            if not fila: return False
            db.delete(fila)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.exception(f"Erro ao remover item da fila: {e}")
            return False

    @staticmethod
    def retry(db: Session, fila_id: int):
        try:
            fila = db.query(Fila).filter(Fila.id == fila_id).first()
            if not fila: return False
            fila.status = "aguardando"
            fila.tentativas = 0
            fila.agendado_para = datetime.utcnow()
            fila.atualizado_em = datetime.utcnow()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.exception(f"Erro ao reenfileirar item: {e}")
            return False

    # NOVA FUNÇÃO: Marcar como publicado para encerrar a sessão
    @staticmethod
    def mark_as_published(db: Session, fila_id: int):
        try:
            fila = db.query(Fila).filter(Fila.id == fila_id).first()
            if not fila: return False
            fila.status = "publicado"
            fila.publicado_em = datetime.utcnow()
            fila.atualizado_em = datetime.utcnow()
            db.commit()
            return True
        except Exception as e:
            logger.exception(f"Erro ao marcar como publicado: {e}")
            return False

queue_service = QueueService()