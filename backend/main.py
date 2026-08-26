import asyncio
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

# =========================================================
# 1. IMPORTS INICIAIS E LOGGING (Essencial estar no topo)
# =========================================================
# Importamos o logger primeiro para que possamos registrar o processo de inicialização
try:
    from backend.logging import logger
except ImportError:
    # Fallback caso o logger não seja encontrado durante a compilação/teste
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("backend")

# =========================================================
# 2. FIXES PARA WINDOWS E PLAYWRIGHT
# =========================================================
# Define a pasta correta do Playwright para cada sistema operacional.
# No Render/Linux, isso deve apontar para ~/.cache/ms-playwright e não para AppData\Local.
def get_playwright_browsers_path() -> str:
    home = Path.home()
    if sys.platform.startswith("win"):
        return str(home / "AppData" / "Local" / "ms-playwright")
    if sys.platform == "darwin":
        return str(home / "Library" / "Caches" / "ms-playwright")
    return str(home / ".cache" / "ms-playwright")

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = get_playwright_browsers_path()
logger.info(f"PLAYWRIGHT_BROWSERS_PATH={os.environ['PLAYWRIGHT_BROWSERS_PATH']}")

# Windows Async Loop Fix
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# =========================================================
# 3. DETECÇÃO DE CAMINHOS (Sincronia entre Dev e .EXE)
# =========================================================
if getattr(sys, 'frozen', False):
    # Se estiver rodando como executável (.exe)
    # BASE_DIR: Pasta onde o .exe está localizado (Para arquivos graváveis: DB, Images)
    BASE_DIR = Path(sys.executable).parent
    # BUNDLE_DIR: Pasta temporária interna do PyInstaller (Para arquivos embutidos: .env, dist)
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    # Se estiver rodando via python (Desenvolvimento)
    BASE_DIR = Path(__file__).resolve().parent.parent
    BUNDLE_DIR = BASE_DIR

# --- CARREGAMENTO DO .ENV ---
# Tenta carregar do pacote embutido primeiro, depois da pasta externa
env_path_internal = BUNDLE_DIR / ".env"
env_path_external = BASE_DIR / ".env"

if env_path_internal.exists():
    load_dotenv(dotenv_path=env_path_internal)
    logger.info(f"✅ API Key carregada do pacote embutido")
elif env_path_external.exists():
    load_dotenv(dotenv_path=env_path_external)
    logger.info(f"✅ API Key carregada de arquivo externo")
else:
    logger.error("❌ API Key não encontrada! O sistema não funcionará corretamente.")

# =========================================================
# 4. IMPORTS DO BACKEND (Depois do load_dotenv para carregar as keys)
# =========================================================
from backend.config import settings
from backend.database import init_db
from backend.api.routes import router
from backend.browser_manager import browser_manager

logger.info(f"📂 Diretório Raiz (Escrita): {BASE_DIR}")
logger.info(f"📦 Diretório Interno (Leitura): {BUNDLE_DIR}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando AS Marketplace Bot SaaS...")
    try:
        init_db()
        logger.info("✅ Banco de dados local inicializado")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco: {e}")

    try:
        await browser_manager.start()
        logger.info("✅ Browser Manager iniciado")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar Browser Manager: {e}")

    yield

    logger.info("Stopping server... limpando sessões do browser")
    await browser_manager.stop()
    logger.info("✅ Browser Manager encerrado com sucesso")

app = FastAPI(
    title="AS Marketplace Bot SaaS",
    description="API backend para extração, revisão e publicação de imóveis",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

# =========================================================
# 5. STATIC FILES & FRONTEND INTEGRATION
# =========================================================

# 1. Pasta de Imagens — Sempre ao lado do .exe (gravável)
IMAGES_DIR = BASE_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")
logger.info(f"🖼️  Servindo imagens de: {IMAGES_DIR}")

# 2. Pasta do Frontend Compilado
# Se for .exe, tenta pegar da pasta embutida (BUNDLE_DIR), senão da pasta raiz (BASE_DIR)
BUILD_DIR = BUNDLE_DIR / "dist" if (getattr(sys, 'frozen', False) and (BUNDLE_DIR / "dist").exists()) else (BASE_DIR / "dist")

if BUILD_DIR.exists() and any(BUILD_DIR.iterdir()):
    app.mount("/", StaticFiles(directory=str(BUILD_DIR), html=True), name="frontend")
    logger.info(f"🌐 Frontend carregado com sucesso de: {BUILD_DIR}")
else:
    logger.warning(f"⚠️ Pasta 'dist' não encontrada em {BUILD_DIR}. O site não será servido.")

@app.get("/")
async def root_info():
    if BUILD_DIR.exists():
        index_file = BUILD_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

    return {
        "status": "ok",
        "service": "AS Marketplace Bot",
        "message": "Backend running. Frontend is served by Vercel in production.",
        "health": "/health",
        "docs": "/docs"
    }

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    if full_path.startswith("api") or full_path.startswith("static"):
        raise HTTPException(status_code=404, detail="Not Found")

    if BUILD_DIR.exists():
        index_file = BUILD_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Frontend not available")

@app.get("/health")
async def health_check():
    return {"status": "ok", "browser_active": browser_manager._playwright is not None}

if __name__ == "__main__":
    import uvicorn
    # Rodando o app sem 'reload' para evitar problemas com o .exe
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
