from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, AnyUrl, Field


# =========================================================
# IMÓVEL BASE
# =========================================================

class ImovelBase(BaseModel):
    url: str
    titulo: str
    preco: float

    descricao: Optional[str] = None
    endereco: Optional[str] = None

    quartos: int = 0
    banheiros: int = 0
    garagem: int = 0
    area: int = 0

    # Evita bug de lista mutável compartilhada
    imagens_json: List[str] = Field(default_factory=list)

    model_config = {
        "from_attributes": True
    }


# =========================================================
# CREATE
# =========================================================

class ImovelCreate(ImovelBase):
    pass


# =========================================================
# UPDATE
# =========================================================

class ImovelUpdate(BaseModel):
    titulo: Optional[str] = None
    preco: Optional[float] = None

    descricao: Optional[str] = None
    endereco: Optional[str] = None

    quartos: Optional[int] = None
    banheiros: Optional[int] = None
    garagem: Optional[int] = None
    area: Optional[int] = None

    imagens_json: Optional[List[str]] = None

    model_config = {
        "from_attributes": True
    }


# =========================================================
# RESPONSE
# =========================================================

class ImovelResponse(ImovelBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    model_config = {
        "from_attributes": True
    }


# =========================================================
# FILA BASE
# =========================================================

class FilaBase(BaseModel):
    imovel_id: int

    status: str = "aguardando"
    tentativas: int = 0

    agendado_para: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


# =========================================================
# FILA RESPONSE
# =========================================================

class FilaResponse(FilaBase):
    id: int

    publicado_em: Optional[datetime] = None
    url_facebook: Optional[str] = None
    mensagem_erro: Optional[str] = None

    criado_em: datetime
    atualizado_em: datetime

    imovel: Optional[ImovelResponse] = None

    model_config = {
        "from_attributes": True
    }


# =========================================================
# DASHBOARD
# =========================================================

class DashboardStats(BaseModel):
    total_extraidos: int = 0
    total_publicados: int = 0
    total_erros: int = 0
    total_bloqueios: int = 0
    fila_pendente: int = 0
    taxa_sucesso: float = 0.0

    model_config = {
        "from_attributes": True
    }


# =========================================================
# EXTRAÇÃO
# =========================================================

class ExtractPayload(BaseModel):
    urls: List[AnyUrl]

    model_config = {
        "from_attributes": True
    }


# =========================================================
# PUBLICAÇÃO
# =========================================================

class PublishRequest(BaseModel):
    fila_id: int

    model_config = {
        "from_attributes": True
    }