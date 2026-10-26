"""Desktop worker that runs reviewable browser sessions on the customer's PC."""

import asyncio
import os
import sys
import time
from urllib.parse import urlparse

import requests

from backend.browser_manager import browser_manager
from backend.config import settings
from backend.logging import logger
from backend.services.facebook_handler import publicar_imovel


POLL_INTERVAL_SECONDS = 5
REVIEW_POLL_INTERVAL_SECONDS = 5
HEARTBEAT_INTERVAL_SECONDS = 30
FACEBOOK_LOGIN_TIMEOUT_SECONDS = 15 * 60


class DesktopAgentClient:
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"}

    def _request(self, method: str, path: str, payload: dict | None = None):
        response = requests.request(
            method,
            f"{self.api_url}/api{path}",
            headers=self.headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    async def request(self, method: str, path: str, payload: dict | None = None):
        return await asyncio.to_thread(self._request, method, path, payload)


def _agent_config():
    api_url = os.getenv("DESKTOP_AGENT_API_URL", "").strip()
    token = settings.desktop_agent_token.strip()
    parsed_url = urlparse(api_url)
    if not api_url or parsed_url.scheme not in ("https", "http") or not parsed_url.netloc:
        raise RuntimeError("Defina DESKTOP_AGENT_API_URL com a URL pública da API")
    if parsed_url.scheme != "https" and parsed_url.hostname not in ("localhost", "127.0.0.1"):
        raise RuntimeError("A API remota do agente deve usar HTTPS")
    if not token:
        raise RuntimeError("Defina DESKTOP_AGENT_TOKEN no .env deste computador")
    return DesktopAgentClient(api_url, token)


async def _wait_for_operator_confirmation(client: DesktopAgentClient, fila_id: int):
    while True:
        try:
            result = await client.request("GET", f"/agent/jobs/{fila_id}")
            status = result.get("status")
            if status == "publicado":
                logger.info("Publicação %s confirmada no dashboard", fila_id)
                return
            if status != "aguardando_confirmacao":
                logger.warning(
                    "Tarefa %s saiu da etapa de confirmação (status=%s)",
                    fila_id,
                    status,
                )
                return
        except requests.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else None
            if status_code == 404:
                logger.warning("Tarefa %s não existe mais na fila", fila_id)
                return
            if status_code in (401, 403):
                raise RuntimeError("API recusou a autenticação do agente desktop") from error
            logger.warning(
                "API retornou HTTP %s ao consultar tarefa %s; tentando novamente",
                status_code,
                fila_id,
            )
        except requests.RequestException as error:
            logger.warning(
                "Falha ao consultar confirmação da tarefa %s (%s); tentando novamente",
                fila_id,
                error.__class__.__name__,
            )
        await asyncio.sleep(REVIEW_POLL_INTERVAL_SECONDS)


async def _keep_job_alive(client: DesktopAgentClient, fila_id: int):
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
        try:
            await client.request("POST", f"/agent/jobs/{fila_id}/heartbeat")
        except requests.HTTPError as error:
            if error.response is not None and error.response.status_code == 409:
                logger.warning("A tarefa %s não está mais ativa para este agente", fila_id)
                return
            logger.warning("Falha no heartbeat da tarefa %s", fila_id)
        except requests.RequestException as error:
            logger.warning(
                "Sem conexão para heartbeat da tarefa %s (%s)",
                fila_id,
                error.__class__.__name__,
            )


async def _ensure_facebook_login(page):
    await page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
    deadline = time.monotonic() + FACEBOOK_LOGIN_TIMEOUT_SECONDS
    announced = False
    while time.monotonic() < deadline:
        current_url = page.url.lower()
        login_form = page.locator('input[name="email"]')
        login_visible = await login_form.count() > 0 and await login_form.first.is_visible()
        requires_login = (
            "facebook.com/login" in current_url
            or "facebook.com/checkpoint" in current_url
            or login_visible
        )
        if not requires_login:
            return
        if not announced:
            logger.info(
                "Entre no Facebook na janela aberta para este perfil; "
                "o agente aguardará até 15 minutos."
            )
            announced = True
        await asyncio.sleep(2)
    raise TimeoutError("Login do Facebook não concluído dentro de 15 minutos")


async def run_agent():
    client = _agent_config()
    await browser_manager.start()
    logger.info("Agente desktop conectado à API. O navegador será aberto neste computador.")
    try:
        while True:
            try:
                response = await client.request("POST", "/agent/jobs/claim")
            except requests.RequestException as error:
                logger.warning(
                    "API indisponível (%s); nova tentativa em %ss",
                    error.__class__.__name__,
                    POLL_INTERVAL_SECONDS,
                )
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue

            job = response.get("job")
            if not job:
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue

            fila_id = job["fila_id"]
            imovel_id = job["imovel_id"]
            logger.info("Tarefa %s recebida para o imóvel %s", fila_id, imovel_id)
            heartbeat = asyncio.create_task(_keep_job_alive(client, fila_id))
            try:
                session = await browser_manager.create_session("desktop-agent")
                page = await session.new_page()
                await _ensure_facebook_login(page)
                ready_for_review = await publicar_imovel(
                    page=page,
                    imovel_id=imovel_id,
                    fila_id=fila_id,
                    dados_imovel=job["dados_imovel"],
                )
                await client.request(
                    "POST",
                    f"/agent/jobs/{fila_id}/result",
                    {
                        "ready_for_review": ready_for_review,
                        "error": None if ready_for_review else "Agente não conseguiu preparar o anúncio",
                    },
                )
                if ready_for_review:
                    logger.info(
                        "Confira a janela do Facebook neste computador; publique manualmente "
                        "e confirme no dashboard."
                    )
                    await _wait_for_operator_confirmation(client, fila_id)
                else:
                    logger.error(
                        "Tarefa %s falhou. Corrija o problema no computador do agente "
                        "e reenvie o item pelo dashboard.",
                        fila_id,
                    )
            except Exception as error:
                logger.exception("Falha local na tarefa %s: %s", fila_id, error)
                try:
                    await client.request(
                        "POST",
                        f"/agent/jobs/{fila_id}/result",
                        {
                            "ready_for_review": False,
                            "error": f"Erro no agente desktop: {error.__class__.__name__}",
                        },
                    )
                except requests.RequestException:
                    logger.exception("Não foi possível reportar a falha da tarefa %s", fila_id)
            finally:
                heartbeat.cancel()
                try:
                    await heartbeat
                except asyncio.CancelledError:
                    pass
                await browser_manager.close_session("desktop-agent")
    finally:
        await browser_manager.stop()


def main():
    if settings.browser_headless:
        raise SystemExit(
            "O agente precisa do Chromium visível. Defina BROWSER_HEADLESS=false "
            "no .env do computador do agente."
        )
    if sys.platform.startswith("linux") and not (
        os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY")
    ):
        raise SystemExit(
            "O agente precisa de um desktop com interface gráfica para mostrar o Chromium. "
            "Execute-o no computador do cliente, não no servidor headless."
        )
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        logger.info("Agente desktop encerrado pelo usuário")
    except RuntimeError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
