import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .config import settings

def setup_logger(name: str):
    Path(settings.logs_dir).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 1. Handler para Arquivo
    file_path = Path(settings.logs_dir) / "backend.log"
    handler_file = RotatingFileHandler(
        file_path,
        maxBytes=5_242_880,
        backupCount=5,
        encoding="utf-8"
    )
    handler_file.setFormatter(formatter)

    # 2. Handler para Console (Terminal)
    handler_console = logging.StreamHandler()
    handler_console.setFormatter(formatter)

    logger.addHandler(handler_file)
    logger.addHandler(handler_console)

    return logger

# Criamos a instância do logger
logger = setup_logger("backend")

# --- AQUI ESTÁ O SEGREDO ---
# Importamos o handler depois de criar o logger para evitar importação circular
from backend.services.log_broadcaster import WebSocketHandler

# Criamos o handler de WebSocket e adicionamos ao logger
ws_handler = WebSocketHandler()
ws_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s")) # Formato mais limpo para o UI
logger.addHandler(ws_handler)
