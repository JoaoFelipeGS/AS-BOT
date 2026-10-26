from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings
from .models import Base

def get_engine():
    database_url = make_url(settings.database_url)

    if database_url.get_backend_name() == "sqlite":
        db_path_str = database_url.database
        is_sqlite_uri = database_url.query.get("uri") in (True, "true", "1")
        if db_path_str not in (None, "", ":memory:") and not is_sqlite_uri:
            db_path = Path(db_path_str).expanduser().resolve()
            db_path.parent.mkdir(parents=True, exist_ok=True)
            database_url = database_url.set(database=str(db_path))
            logger.info("Conectando ao banco de dados SQLite: %s", db_path)

            return create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=NullPool,
            )

        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
        )

    return create_engine(settings.database_url, pool_pre_ping=True)

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
