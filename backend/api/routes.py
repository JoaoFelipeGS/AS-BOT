import os
import re
import sys
import asyncio
import json
import hmac
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import List

from ..schemas import (
    DashboardStats,
    ExtractPayload,
    ImovelResponse,
    ImovelUpdate,
    FilaResponse,
    PublishRequest,
)
# IMPORTANTE: Adicionei o Fila aqui para podermos filtrar a lista
from ..database import SessionLocal
from ..models import Imovel, Fila 
from ..services.extractor_service import ExtractorService
from ..services.queue_service import QueueService
from backend.services.log_broadcaster import log_broadcaster
from backend.logging import logger
from backend.auth import create_token, require_auth
from backend.config import settings
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str


class DesktopAgentResult(BaseModel):
    ready_for_review: bool
    error: str | None = None


@router.post("/login")
def login(payload: LoginRequest):
    if payload.username != settings.admin_username or payload.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    return {
        "token": create_token(payload.username),
        "username": payload.username,
        "message": "Login realizado com sucesso"
    }

# =========================================================
# DETECÇÃO DE CAMINHO (mesma lógica do main.py)
# =========================================================
if getattr(sys, 'frozen', False):
    # Rodando como .exe — pasta onde o executável está
    BASE_DIR = Path(sys.executable).parent
else:
    # Rodando como script Python normal
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
# =========================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _normalize_imagens(imagens):
    if not imagens:
        return []

    if isinstance(imagens, str):
        try:
            imagens = json.loads(imagens)
        except json.JSONDecodeError:
            imagens = [imagens]

    if not isinstance(imagens, list):
        return []

    return [imagem for imagem in imagens if isinstance(imagem, str) and imagem.startswith(('http://', 'https://'))]

def _prepare_imovel(imovel: Imovel):
    if not imovel: return None
    imovel.imagens_json = _normalize_imagens(imovel.imagens_json)
    return imovel


async def require_desktop_agent(
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    configured_token = settings.desktop_agent_token.strip()
    if not configured_token:
        raise HTTPException(status_code=503, detail="Agente desktop não configurado no servidor")
    scheme, _, token = (authorization or "").partition(" ")
    if (
        scheme.lower() != "bearer"
        or not token
        or not hmac.compare_digest(token, configured_token)
    ):
        raise HTTPException(status_code=401, detail="Token do agente desktop inválido")
    return True


def _agent_job_payload(fila: Fila):
    imovel = fila.imovel
    if not imovel:
        raise HTTPException(status_code=409, detail="Imóvel da tarefa não encontrado")
    return {
        "fila_id": fila.id,
        "imovel_id": imovel.id,
        "dados_imovel": {
            "preco": imovel.preco,
            "descricao": imovel.descricao,
            "quartos": imovel.quartos,
            "banheiros": imovel.banheiros,
            "garagem": imovel.garagem,
            "imagens_json": _normalize_imagens(imovel.imagens_json),
            "url": imovel.url,
        },
    }

@router.get("/dashboard", response_model=DashboardStats)
def dashboard_overview(db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    return QueueService.dashboard_stats(db)

@router.post("/extract", response_model=List[ImovelResponse])
async def extract_listings(payload: ExtractPayload, db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    del db
    # Um Chromium por vez evita que o plano gratuito do Render encerre os
    # contextos por falta de memória durante lotes maiores.
    semaphore = asyncio.Semaphore(1)
    urls = []
    for raw_url in payload.urls:
        url = str(raw_url).strip()
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc and url not in urls:
            urls.append(url)

    if not urls:
        raise HTTPException(status_code=422, detail="Nenhuma URL válida foi enviada")

    logger.info(f"Iniciando lote de extração: {len(urls)} URL(s), concorrência 2")

    async def extract_one(url):
        async with semaphore:
            local_db = SessionLocal()
            try:
                imovel = await ExtractorService.extract_and_save(str(url), local_db)
                return _prepare_imovel(imovel) if imovel else None
            except asyncio.TimeoutError:
                logger.error(f"Tempo limite excedido na extração: {url}")
            except Exception as e:
                logger.exception(f"Erro ao extrair URL {url}: {e}")
            finally:
                local_db.close()
            return None

    extracted = await asyncio.gather(*(extract_one(url) for url in urls), return_exceptions=False)
    results = [item for item in extracted if item is not None]
    if not results:
        raise HTTPException(status_code=422, detail="Nenhum imóvel extraído com sucesso")
    return results

# =============================================================================
# LISTAR APENAS IMÓVEIS QUE NÃO ESTÃO NA FILA
# =============================================================================
@router.get("/imoveis", response_model=List[ImovelResponse])
def list_imoveis(db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    try:
        # Subquery para pegar todos os IDs de imóveis que já estão na fila
        imoveis_na_fila = select(Fila.imovel_id)
        
        # Filtra a tabela Imovel: pega apenas quem NÃO está na subquery da fila
        imoveis = db.query(Imovel).filter(
            ~Imovel.id.in_(imoveis_na_fila)
        ).order_by(Imovel.criado_em.desc()).all()
        
        return [_prepare_imovel(imovel) for imovel in imoveis]
    except Exception as e:
        logger.exception(f"Erro ao listar imóveis: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao listar imóveis")

@router.delete("/imoveis/{imovel_id}")
def delete_imovel(imovel_id: int, db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    try:
        imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
        if not imovel:
            raise HTTPException(status_code=404, detail="Imóvel não encontrado")
        db.delete(imovel)
        db.commit()
        return {"ok": True, "message": "Imóvel excluído com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Erro ao excluir imóvel: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao excluir imóvel")

@router.get("/imoveis/{imovel_id}", response_model=ImovelResponse)
def get_imovel(imovel_id: int, db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    return _prepare_imovel(imovel)

@router.patch("/imoveis/{imovel_id}", response_model=ImovelResponse)
def update_imovel(imovel_id: int, payload: ImovelUpdate, db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    try:
        update_data = payload.dict(exclude_unset=True)
        if "imagens_json" in update_data:
            update_data["imagens_json"] = json.dumps(update_data["imagens_json"], ensure_ascii=False)
        for field, value in update_data.items():
            setattr(imovel, field, value)
        imovel.atualizado_em = datetime.utcnow()
        db.commit()
        db.refresh(imovel)
        return _prepare_imovel(imovel)
    except Exception as e:
        db.rollback()
        logger.exception(f"Erro ao atualizar imóvel: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar imóvel")

@router.post("/imoveis/{imovel_id}/queue", response_model=FilaResponse)
def add_imovel_to_queue(imovel_id: int, db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    try:
        fila = QueueService.add_to_queue(db, imovel_id)
        if not fila:
            raise HTTPException(status_code=500, detail="Falha ao adicionar à fila")
        if fila.imovel:
            fila.imovel = _prepare_imovel(fila.imovel)
        return fila
    except HTTPException: raise
    except Exception as e:
        logger.exception(f"Erro ao adicionar à fila: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao adicionar à fila")

@router.get("/fila", response_model=List[FilaResponse])
def list_queue(db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    try:
        fila = QueueService.list_queue(db)
        for item in fila:
            if item.imovel: item.imovel = _prepare_imovel(item.imovel)
        return fila
    except Exception as e:
        logger.exception(f"Erro ao listar fila: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao listar fila")

@router.get("/fila/{fila_id}", response_model=FilaResponse)
def get_queue_item(fila_id: int, db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    fila = QueueService.get_item(db, fila_id)
    if not fila:
        raise HTTPException(status_code=404, detail="Item da fila não encontrado")
    if fila.imovel:
        fila.imovel = _prepare_imovel(fila.imovel)
    return fila

@router.delete("/fila/{fila_id}")
def delete_queue_item(fila_id: int, db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    try:
        success = QueueService.delete_queue(db, fila_id)
        if not success:
            raise HTTPException(status_code=404, detail="Item da fila não encontrado")
        return {"ok": True}
    except HTTPException: raise
    except Exception as e:
        logger.exception(f"Erro ao remover item da fila: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao remover item da fila")

@router.post("/fila/publish")
async def publish_item(
    payload: PublishRequest,
    db: Session = Depends(get_db),
    _user: str = Depends(require_auth),
):
    if not settings.desktop_agent_token.strip():
        raise HTTPException(
            status_code=503,
            detail="Configure DESKTOP_AGENT_TOKEN e conecte o agente desktop antes de publicar",
        )
    try:
        fila = db.query(Fila).filter(Fila.id == payload.fila_id).first()
        if not fila:
            raise HTTPException(status_code=404, detail="Item da fila não encontrado")
        if fila.status in ("aguardando_agente", "processando_agente", "aguardando_confirmacao"):
            return {"ok": True, "status": fila.status}
        if fila.status not in ("aguardando", "erro"):
            raise HTTPException(status_code=409, detail=f"Item não pode ser publicado no status '{fila.status}'")

        result = db.execute(
            update(Fila)
            .where(Fila.id == payload.fila_id, Fila.status == fila.status)
            .values(
                status="aguardando_agente",
                mensagem_erro=None,
                atualizado_em=datetime.utcnow(),
            )
        )
        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(status_code=409, detail="Item da fila foi atualizado simultaneamente")
        db.commit()
        logger.info(f"Publicação {payload.fila_id} encaminhada ao agente desktop")
        return {"ok": True, "status": "aguardando_agente"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Erro ao encaminhar publicação ao agente desktop: {e}")
        raise HTTPException(status_code=500, detail="Erro ao encaminhar publicação")


@router.post("/agent/jobs/claim")
def claim_desktop_job(
    db: Session = Depends(get_db),
    _agent: bool = Depends(require_desktop_agent),
):
    stale_at = datetime.utcnow() - timedelta(seconds=120)
    db.execute(
        update(Fila)
        .where(
            Fila.status.in_(("processando_agente", "aguardando_confirmacao")),
            Fila.atualizado_em < stale_at,
        )
        .values(
            status="erro",
            mensagem_erro="Agente desktop desconectado. Reenvie a publicação para tentar novamente.",
            atualizado_em=datetime.utcnow(),
        )
    )
    db.commit()

    for _ in range(3):
        fila = (
            db.query(Fila)
            .filter(Fila.status == "aguardando_agente")
            .order_by(Fila.agendado_para.asc(), Fila.id.asc())
            .first()
        )
        if not fila:
            return {"job": None}
        fila_id = fila.id
        result = db.execute(
            update(Fila)
            .where(Fila.id == fila_id, Fila.status == "aguardando_agente")
            .values(
                status="processando_agente",
                tentativas=(Fila.tentativas + 1),
                atualizado_em=datetime.utcnow(),
                mensagem_erro=None,
            )
        )
        if result.rowcount == 1:
            db.commit()
            claimed = db.query(Fila).filter(Fila.id == fila_id).first()
            return {"job": _agent_job_payload(claimed)}
        db.rollback()
    return {"job": None}


@router.get("/agent/jobs/{fila_id}")
def get_desktop_job_status(
    fila_id: int,
    db: Session = Depends(get_db),
    _agent: bool = Depends(require_desktop_agent),
):
    fila = db.query(Fila).filter(Fila.id == fila_id).first()
    if not fila:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    if fila.status == "aguardando_confirmacao":
        fila.atualizado_em = datetime.utcnow()
        db.commit()
    return {"fila_id": fila.id, "status": fila.status, "mensagem_erro": fila.mensagem_erro}


@router.post("/agent/jobs/{fila_id}/heartbeat")
def heartbeat_desktop_job(
    fila_id: int,
    db: Session = Depends(get_db),
    _agent: bool = Depends(require_desktop_agent),
):
    result = db.execute(
        update(Fila)
        .where(
            Fila.id == fila_id,
            Fila.status.in_(("processando_agente", "aguardando_confirmacao")),
        )
        .values(atualizado_em=datetime.utcnow())
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="Tarefa não está ativa para este agente")
    db.commit()
    return {"ok": True}


@router.post("/agent/jobs/{fila_id}/result")
def report_desktop_job_result(
    fila_id: int,
    payload: DesktopAgentResult,
    db: Session = Depends(get_db),
    _agent: bool = Depends(require_desktop_agent),
):
    fila = db.query(Fila).filter(Fila.id == fila_id).first()
    if not fila:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    if fila.status != "processando_agente":
        raise HTTPException(status_code=409, detail="Tarefa não está sendo processada pelo agente")

    fila.status = "aguardando_confirmacao" if payload.ready_for_review else "erro"
    fila.mensagem_erro = None if payload.ready_for_review else (payload.error or "Agente não conseguiu preparar o anúncio")[:1000]
    fila.atualizado_em = datetime.utcnow()
    db.commit()
    logger.info(
        "Agente desktop terminou tarefa %s: %s",
        fila_id,
        fila.status,
    )
    return {"ok": True, "status": fila.status}

@router.post("/fila/retry/{fila_id}")
def retry_item(fila_id: int, db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    try:
        success = QueueService.retry(db, fila_id)
        if not success:
            raise HTTPException(status_code=404, detail="Item da fila não encontrado")
        return {"ok": True}
    except HTTPException: raise
    except Exception as e:
        logger.exception(f"Erro ao reenfileirar item: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao reenfileirar item")

@router.post("/fila/confirm/{fila_id}")
async def confirm_publication(fila_id: int, db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    try:
        fila = db.query(Fila).filter(Fila.id == fila_id).first()
        if not fila:
            raise HTTPException(status_code=404, detail="Item da fila não encontrado")
        if fila.status != "aguardando_confirmacao":
            raise HTTPException(status_code=409, detail="Item ainda não está pronto para confirmação")
        success = QueueService.mark_as_published(db, fila_id)
        if not success:
            raise HTTPException(status_code=404, detail="Item da fila não encontrado")

        return {"ok": True, "message": "Publicação confirmada."}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao confirmar publicação: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao confirmar publicação")

@router.websocket("/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept() 
    await log_broadcaster.connect(websocket)
    logger.info("WebSocket conectado para logs")
    try:
        while True:
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        await log_broadcaster.disconnect(websocket)
    except Exception as e:
        logger.exception(f"Erro no websocket de logs: {str(e)}")
        try: 
            await log_broadcaster.disconnect(websocket)
        except Exception: 
            pass