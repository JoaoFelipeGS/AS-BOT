import asyncio
import os
import sys
from typing import Dict
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext
from .config import settings
import logging

logger = logging.getLogger("bot")


def get_playwright_browsers_path() -> str:
    configured = os.getenv("PLAYWRIGHT_BROWSERS_PATH")
    if configured and configured.strip():
        return configured.strip()

    render_project = Path("/opt/render/project")
    if os.getenv("RENDER") and render_project.exists():
        return str(render_project / ".cache" / "ms-playwright")

    home = Path.home()
    if sys.platform.startswith("win"):
        return str(home / "AppData" / "Local" / "ms-playwright")
    if sys.platform == "darwin":
        return str(home / "Library" / "Caches" / "ms-playwright")
    return str(home / ".cache" / "ms-playwright")

class BrowserSession:
    def __init__(self, context: BrowserContext):
        self.context = context

    async def new_page(self):
        return await self.context.new_page()

    async def close(self):
        await self.context.close()

class BrowserManager:
    def __init__(self):
        self.sessions: Dict[str, BrowserSession] = {}
        self._lock = asyncio.Lock()
        self._playwright = None

    async def start(self):
        if sys.platform.startswith("win"):
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception:
                pass

        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = get_playwright_browsers_path()

        if self._playwright is None:
            self._playwright = await async_playwright().start()

    async def stop(self):
        for session in list(self.sessions.values()):
            await session.close()
        self.sessions.clear()
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def create_session(self, session_id: str):
        await self.start()
        async with self._lock:
            if session_id in self.sessions:
                return self.sessions[session_id]

            profile_dir = Path(settings.persistent_profile) / session_id
            profile_dir.mkdir(parents=True, exist_ok=True)

            context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                channel="chromium",
                headless=settings.browser_headless,
                viewport=None,
                slow_mo=settings.browser_slow_mo,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            session = BrowserSession(context)
            self.sessions[session_id] = session
            return session

    async def close_session(self, session_id: str):
        """Fecha e remove a sessão do dicionário — use no confirm."""
        session = self.sessions.pop(session_id, None)
        if session:
            try:
                await session.close()
            except Exception:
                pass

    async def get_session(self, session_id: str):
        session = self.sessions.get(session_id)
        if session is None:
            return None
        # Verifica se o contexto ainda está vivo
        try:
            _ = session.context.pages  # lança se fechado
            return session
        except Exception:
            self.sessions.pop(session_id, None)
            return None

browser_manager = BrowserManager()