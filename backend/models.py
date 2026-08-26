from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Imovel(Base):
    __tablename__ = "imoveis"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), unique=True, nullable=False)
    titulo = Column(String(300), nullable=False)
    preco = Column(Float, default=0)
    descricao = Column(Text)
    endereco = Column(String(500))
    quartos = Column(Integer, default=0)
    banheiros = Column(Integer, default=0)
    garagem = Column(Integer, default=0)
    area = Column(Integer, default=0)
    imagens_json = Column(JSON, default=[])
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento com a Fila (Atualizado para referenciar a classe 'Fila')
    fila = relationship("Fila", back_populates="imovel", cascade="all, delete-orphan")


class Fila(Base): # Renomeado de FilaPublicacao para Fila para bater com o routes.py
    __tablename__ = "fila_publicacao" # Mantivemos o nome da tabela para não quebrar o banco
    id = Column(Integer, primary_key=True, index=True)
    imovel_id = Column(Integer, ForeignKey("imoveis.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="aguardando")
    tentativas = Column(Integer, default=0)
    agendado_para = Column(DateTime)
    publicado_em = Column(DateTime)
    url_facebook = Column(String(500))
    mensagem_erro = Column(Text)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento com o Imóvel
    imovel = relationship("Imovel", back_populates="fila")


class LogItem(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(100))
    mensagem = Column(Text)
    detalhes = Column(JSON, default={})
    criado_em = Column(DateTime, default=datetime.utcnow)


class Bloqueio(Base):
    __tablename__ = "bloqueios"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(100))
    ativo = Column(Boolean, default=True)
    detectado_em = Column(DateTime, default=datetime.utcnow)
    desbloqueado_em = Column(DateTime)
    motivo = Column(Text)
