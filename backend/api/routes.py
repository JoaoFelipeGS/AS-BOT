import os
import re
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
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
from ..services.publisher_service import PublisherService
from ..services.queue_service import QueueService
from backend.services.log_broadcaster import log_broadcaster
from backend.logging import logger
from backend.browser_manager import browser_manager
from backend.auth import create_token, require_auth
from backend.config import settings
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

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

    # 1. EXTRAIR O ID DA PASTA
    folder_id = None
    raw_text = str(imagens)
    match = re.search(r'images[\\/]+([a-zA-Z0-9_-]+)', raw_text)
    if match:
        folder_id = match.group(1)
    
    if not folder_id:
        return []

    # 2. LOCALIZAR A PASTA NO DISCO
    # images/ fica sempre ao lado do .exe (ou raiz do projeto em dev)
    try:
        images_root = BASE_DIR / "images"
        target_folder = images_root / folder_id

        if target_folder.exists() and target_folder.is_dir():
            extensoes_validas = ('.jpg', '.jpeg', '.png', '.webp')
            arquivos_na_pasta = [
                f.name for f in target_folder.iterdir() 
                if f.suffix.lower() in extensoes_validas
            ]
            
            if arquivos_na_pasta:
                urls_finais = [f"/static/images/{folder_id}/{foto}" for foto in arquivos_na_pasta]
                return urls_finais
        else:
            logger.warning(f"Pasta de imagens não encontrada: {target_folder}")
    except Exception as e:
        logger.error(f"Erro ao ler pasta de imagens: {e}")

    return []

def _prepare_imovel(imovel: Imovel):
    if not imovel: return None
    imovel.imagens_json = _normalize_imagens(imovel.imagens_json)
    return imovel

@router.get("/dashboard", response_model=DashboardStats)
def dashboard_overview(db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    return QueueService.dashboard_stats(db)

@router.post("/extract", response_model=List[ImovelResponse])
async def extract_listings(payload: ExtractPayload, db: Session = Depends(get_db), _user: str = Depends(require_auth)):
    results = []
    for url in payload.urls:
        try:
            imovel = await ExtractorService.extract_and_save(str(url), db)
            if imovel:
                results.append(_prepare_imovel(imovel))
        except Exception as e:
            logger.exception(f"Erro ao extrair URL {url}: {str(e)}")
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
        imoveis_na_fila = db.query(Fila.imovel_id).subquery()
        
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
    except Exception as e:
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
async def publish_item(payload: PublishRequest, _user: str = Depends(require_auth)):
    try:
        success = await PublisherService.publish(payload.fila_id)
        if not success:
            raise HTTPException(status_code=500, detail="Falha ao publicar o imóvel")
        return {"ok": True}
    except HTTPException: raise
    except Exception as e:
        logger.exception(f"Erro ao publicar imóvel: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao publicar imóvel")

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
        success = QueueService.mark_as_published(db, fila_id)
        if not success:
            raise HTTPException(status_code=404, detail="Item da fila não encontrado")

        await browser_manager.close_session("admin")

        return {"ok": True, "message": "Publicação confirmada e navegador encerrado."}
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