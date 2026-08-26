import asyncio
import logging
from typing import List
from fastapi import WebSocket
from backend.logging import logger

class LogBroadcaster:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        self.connections.append(websocket)
        # Não usamos logger.info aqui dentro para evitar loop infinito de logs
        print(f"WebSocket registrado no broadcaster. Total: {len(self.connections)}")

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, message: str):
        if not self.connections:
            return
            
        for connection in self.connections.copy():
            try:
                await connection.send_text(message)
            except Exception:
                await self.disconnect(connection)

# Instância global do Broadcaster
log_broadcaster = LogBroadcaster()

# --- A PONTE (O Handler) ---
class WebSocketHandler(logging.Handler):
    """
    Handler customizado que intercepta logs do Python 
    e os envia via WebSocket para o Frontend.
    """
    def emit(self, record):
        log_entry = self.format(record)
        # Como o emit do logging é síncrono e o broadcast é assíncrono,
        # usamos o loop de eventos do asyncio para disparar a tarefa
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(log_broadcaster.broadcast(log_entry))
        except Exception:
            pass
