from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings
from .models import Base

def get_engine():
    database_url = settings.database_url

    if database_url.startswith("sqlite"):
        # --- MELHORIA DE CAMINHO ---
        # Extraímos o caminho do arquivo do banco de dados
        # Ex: sqlite:///./database.db -> ./database.db
        db_path_str = database_url.replace("sqlite:///", "")
        db_path = Path(db_path_str).resolve()
        
        # Garante que a pasta onde o banco vai ficar exista
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Usamos o caminho absoluto para evitar que o SQLite crie 
        # bancos em pastas diferentes dependendo de onde o .exe é aberto
        absolute_url = f"sqlite:///{db_path}"
        
        logger.info(f"🗄️  Conectando ao banco de dados local: {db_path}")
        
        return create_engine(
            absolute_url, 
            connect_args={"check_same_thread": False}, 
            poolclass=NullPool
        )

    # Se for Postgres/Neon, mantém a configuração original
    return create_engine(database_url, pool_pre_ping=True)

# Importamos o logger aqui para evitar importação circular
from backend.logging import logger

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    """Cria as tabelas no arquivo .db caso elas não existam"""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Erro ao criar tabelas do banco de dados: {e}")
